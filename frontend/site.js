const reveal=()=>document.querySelectorAll('.component,.source-list a,.method-steps div').forEach((el,i)=>{el.style.animationDelay=`${i*45}ms`;el.classList.add('reveal')});reveal();
