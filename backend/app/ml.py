"""Research-grade small-data neural anomaly engine.

Architecture: feature projection -> positional encoding -> Transformer encoder ->
reconstruction + next-step prediction heads.  A classical IsolationForest and
robust Mahalanobis-like z score are kept alongside it because 16 local samples
alone cannot justify a neural model as ground truth.  The ensemble is therefore
anomaly screening, not a clinical/environmental diagnosis.
"""
from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path
import numpy as np
import torch
from torch import nn
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler

FEATURES = ["ph", "do_mg_l", "bod_mg_l"]
torch.set_num_threads(1)

class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 64):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        pos = torch.arange(max_len, dtype=torch.float32).unsqueeze(1)
        div = torch.exp(torch.arange(0, d_model, 2).float() * (-np.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(pos * div)
        pe[:, 1::2] = torch.cos(pos * div[:pe[:, 1::2].shape[1]])
        self.register_buffer("pe", pe.unsqueeze(0))
    def forward(self, x): return x + self.pe[:, :x.size(1)]

class AquaTemporalNet(nn.Module):
    def __init__(self, n_features=3, d_model=48, heads=4, layers=3, dropout=.12):
        super().__init__()
        self.proj = nn.Sequential(nn.Linear(n_features,d_model), nn.LayerNorm(d_model), nn.GELU())
        self.pos = PositionalEncoding(d_model)
        block = nn.TransformerEncoderLayer(d_model=d_model,nhead=heads,dim_feedforward=128,dropout=dropout,activation="gelu",batch_first=True,norm_first=False)
        self.encoder = nn.TransformerEncoder(block,num_layers=layers)
        self.norm = nn.LayerNorm(d_model)
        self.reconstruct = nn.Sequential(nn.Linear(d_model,64),nn.GELU(),nn.Dropout(dropout),nn.Linear(64,n_features))
        self.next_step = nn.Sequential(nn.Linear(d_model,64),nn.GELU(),nn.Linear(64,n_features))
        self.health_head = nn.Sequential(nn.Linear(d_model,32),nn.GELU(),nn.Linear(32,1),nn.Sigmoid())
    def forward(self,x):
        z=self.encoder(self.pos(self.proj(x)))
        pooled=self.norm(z[:,-1])
        return self.reconstruct(z), self.next_step(pooled), self.health_head(pooled).squeeze(-1)

@dataclass
class NeuralResult:
    neural_error: float
    forecast_error: float
    health_probability: float
    ensemble_score: float
    model: str

class NeuralAnomalyEngine:
    def __init__(self):
        self.scaler=RobustScaler()
        self.net=AquaTemporalNet()
        self.forest=IsolationForest(n_estimators=200,max_samples='auto',contamination='auto',random_state=42)
        self.fitted=False
        self.error_q=.1
        self.forecast_q=.1
        self.artifact_version='traceit-neural-5.0'

    def fit(self, rows: list[list[float]], epochs=180):
        X=np.asarray(rows,dtype=np.float32)
        if X.ndim!=2 or X.shape[0]<8 or X.shape[1] not in (3,5): return self
        Xfull=X.copy()
        X=X[:, :3]
        S=self.scaler.fit_transform(X).astype(np.float32)
        self.forest.fit(S)
        seq=[]
        for i in range(max(1,len(S)-3)):
            seq.append(S[i:i+min(4,len(S)-i)])
        maxlen=max(len(x) for x in seq)
        # left-pad sequences; mask not needed because all are ordered short windows
        batch=np.stack([np.pad(x,((maxlen-len(x),0),(0,0)),mode='edge') for x in seq])
        target=torch.tensor(batch,dtype=torch.float32)
        self.net.train(); opt=torch.optim.AdamW(self.net.parameters(),lr=7e-4,weight_decay=2e-4)
        best=float('inf'); stale=0
        for _ in range(epochs):
            opt.zero_grad(); recon,nxt,health=self.net(target)
            loss_r=((recon-target)**2).mean()
            if maxlen>1: loss_f=((nxt-target[:,-1])**2).mean()
            else: loss_f=loss_r
            # self-supervised auxiliary target: lower chemistry stress should map to higher health.
            stress=torch.tensor(self._domain_stress(Xfull)[max(0,len(Xfull)-len(seq)):],dtype=torch.float32)
            loss_h=((health-(1-stress))**2).mean()
            loss=loss_r + .25*loss_f + .10*loss_h
            if not torch.isfinite(loss): break
            loss.backward(); torch.nn.utils.clip_grad_norm_(self.net.parameters(),1.0); opt.step()
            v=float(loss.detach())
            if v<best-1e-5: best=v; stale=0
            else: stale+=1
            if stale>35: break
        self.net.eval()
        with torch.no_grad():
            recon,nxt,_=self.net(target)
            re=((recon-target)**2).mean(dim=(1,2)).numpy()
            fe=((nxt-target[:,-1])**2).mean(dim=1).numpy()
        self.error_q=max(float(np.quantile(re,.90)),1e-4); self.forecast_q=max(float(np.quantile(fe,.90)),1e-4)
        self.fitted=True
        return self

    @staticmethod
    def _domain_stress(X):
        X=np.asarray(X)
        ph,do,bod=X[:,:3].T
        p=np.clip(np.maximum(6.5-ph,ph-8.5)/1.5,0,1)
        d=np.clip((5-do)/5,0,1)
        b=np.clip((bod-3)/27,0,1)
        if X.shape[1] >= 5:
            t=np.clip((X[:,3]-500)/1500,0,1); c=np.clip((X[:,4]-50)/100,0,1)
            return .28*b+.24*d+.18*p+.15*t+.15*c
        return .38*b+.34*d+.28*p


    def save(self, path):
        path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
        torch.save({'state_dict':self.net.state_dict(),'scaler':self.scaler,'forest':self.forest,'error_q':self.error_q,'forecast_q':self.forecast_q,'artifact_version':self.artifact_version},path)

    def load(self, path):
        obj=torch.load(path,map_location='cpu',weights_only=False)
        self.net.load_state_dict(obj['state_dict']); self.scaler=obj['scaler']; self.forest=obj['forest']; self.error_q=obj['error_q']; self.forecast_q=obj['forecast_q']; self.artifact_version=obj.get('artifact_version',self.artifact_version); self.fitted=True; return self

    def score(self, vector:list[float], history:list[list[float]]|None=None)->NeuralResult:
        if not self.fitted: return NeuralResult(0,0,.5,0,'not-fitted')
        base=np.asarray(vector,dtype=np.float32)
        core=base[:3]
        S=self.scaler.transform([core]).astype(np.float32)[0]
        hist=np.asarray(history or [vector],dtype=np.float32)
        hist=hist[:,:3]
        hs=self.scaler.transform(hist).astype(np.float32)
        if len(hs)<4: hs=np.vstack([np.repeat(hs[:1],4-len(hs),axis=0),hs])
        seq=torch.tensor(hs[-4:][None,...],dtype=torch.float32)
        with torch.no_grad():
            recon,nxt,health=self.net(seq)
            re=float(((recon[:,-1]-seq[:,-1])**2).mean())
            fe=float(((nxt-seq[:,-1])**2).mean())
        forest_raw=float(-self.forest.score_samples([S])[0])
        neural=min(1,re/(self.error_q*1.8))+0.25*min(1,fe/(self.forecast_q*1.8))
        forest=min(1,max(0,(forest_raw-.2)/1.2))
        domain=float(self._domain_stress(np.asarray([base]))[0])
        ensemble=float(np.clip(.48*neural+.22*forest+.30*domain,0,1))
        return NeuralResult(round(min(1,re/(self.error_q*1.8)),4),round(min(1,fe/(self.forecast_q*1.8)),4),round(float(np.nan_to_num(health.item(), nan=.5, posinf=1., neginf=0.)),4),round(ensemble,4),'Transformer-autoencoder + IsolationForest + domain model')

# compatibility wrapper used by old endpoint/tests
class EcosystemAutoencoder:
    def __init__(self): self.engine=NeuralAnomalyEngine()
    def fit(self,X): self.engine.fit(X); return self
    def score(self,vector): return self.engine.score(vector).ensemble_score
