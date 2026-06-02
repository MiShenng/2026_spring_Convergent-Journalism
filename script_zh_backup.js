document.addEventListener('DOMContentLoaded', () => {
    
    /* =========================================
       1. 滚动进度条
    ========================================= */
    const progressBar = document.getElementById('scroll-progress-bar');
    
    window.addEventListener('scroll', () => {
        const scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
        const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const scrollPercent = (scrollTop / scrollHeight) * 100;
        progressBar.style.height = scrollPercent + '%';
    });

    /* =========================================
       2. 导航栏自动高亮
    ========================================= */
    const sections = document.querySelectorAll('section.chapter');
    const navLinks = document.querySelectorAll('.nav-links a');

    window.addEventListener('scroll', () => {
        let current = '';
        const scrollY = window.pageYOffset;

        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            // 提前一半视口高度触发高亮，体验更好
            if (scrollY >= (sectionTop - window.innerHeight / 2)) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href').includes(current)) {
                link.classList.add('active');
            }
        });
    });

    /* =========================================
       3. 元素淡入动画 (Intersection Observer)
    ========================================= */
    const fadeElements = document.querySelectorAll('.fade-up');

    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.15 // 元素露出 15% 时触发
    };

    const fadeObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                // 可选：如果希望滑上去再滑下来再次触发动画，可以不调用 unobserve
                // observer.unobserve(entry.target); 
            }
        });
    }, observerOptions);

    fadeElements.forEach(el => fadeObserver.observe(el));

    /* =========================================
       4. 数字递增动画 (配合 Intersection Observer)
    ========================================= */
    const counters = document.querySelectorAll('.counter');
    
    const counterObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = entry.target;
                const endValue = parseInt(target.getAttribute('data-target'));
                const duration = 2000; // 2秒
                const frameRate = 30;
                const totalFrames = Math.round((duration / 1000) * frameRate);
                let currentFrame = 0;
                
                // 简单的 ease-out 缓动算法
                const easeOutQuad = t => t * (2 - t);
                
                const updateCounter = () => {
                    currentFrame++;
                    const progress = easeOutQuad(currentFrame / totalFrames);
                    const currentVal = Math.round(endValue * progress);
                    
                    target.innerText = currentVal;
                    
                    if (currentFrame < totalFrames) {
                        requestAnimationFrame(updateCounter);
                    } else {
                        target.innerText = endValue; // 确保最终值准确
                    }
                };
                
                // 防止重复触发
                if (!target.classList.contains('counted')) {
                    target.classList.add('counted');
                    updateCounter();
                }
            }
        });
    }, { threshold: 0.5 }); // 数字组件完全进入一半视野才开始滚动

    counters.forEach(counter => counterObserver.observe(counter));

});
