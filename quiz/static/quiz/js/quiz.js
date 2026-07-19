document.addEventListener('DOMContentLoaded', function () {
    // --- Mobile Navigation Menu Toggle ---
    const toggleBtn = document.getElementById('mobile-nav-toggle');
    const navMenu = document.querySelector('.nav-menu');
    if (toggleBtn && navMenu) {
        toggleBtn.addEventListener('click', function () {
            toggleBtn.classList.toggle('open');
            navMenu.classList.toggle('active');
        });
    }

    // --- Quiz Playroom Slide Transitions & option items Selection Glow ---
    const quizForm = document.getElementById('quiz-play-form');
    if (quizForm) {
        const slides = document.querySelectorAll('.question-slide');
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        const submitBtn = document.getElementById('submit-btn');
        const currentQSpan = document.getElementById('current-question-num');
        const totalQSpan = document.getElementById('total-questions-num');

        let currentSlide = 0;
        const totalSlides = slides.length;

        if (totalQSpan) totalQSpan.textContent = totalSlides;

        const gridBtns = document.querySelectorAll('.grid-btn');
        
        function clearAllTimers() {
            const timerContainer = document.getElementById('quiz-timer-container');
            const attemptId = timerContainer ? (timerContainer.dataset.attemptId || timerContainer.dataset.quizId || 'demo_mode') : 'demo_mode';
            if (window.sectionsData) {
                window.sectionsData.forEach(sec => {
                    localStorage.removeItem(`timer_timeLeft_${attemptId}_sec_${sec.id}`);
                });
            }
            localStorage.removeItem(`timer_timeLeft_${attemptId}`);
        }

        function showCustomConfirm(title, message, iconHtml, yesText, noText, onConfirm) {
            let overlay = document.getElementById('dynamic-confirm-modal');
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.className = 'confirm-dialog-overlay';
                overlay.id = 'dynamic-confirm-modal';
                overlay.innerHTML = `
                    <div class="confirm-dialog-box">
                        <div class="confirm-dialog-icon" id="dynamic-confirm-icon" style="color: var(--primary-orange);"></div>
                        <h4 class="confirm-dialog-title" id="dynamic-confirm-title"></h4>
                        <p class="confirm-dialog-text" id="dynamic-confirm-text"></p>
                        <div class="confirm-dialog-buttons">
                            <button type="button" class="btn btn-primary" id="dynamic-confirm-yes"></button>
                            <button type="button" class="btn btn-secondary" id="dynamic-confirm-no"></button>
                        </div>
                    </div>
                `;
                document.body.appendChild(overlay);
            }
            
            document.getElementById('dynamic-confirm-icon').innerHTML = iconHtml;
            document.getElementById('dynamic-confirm-title').textContent = title;
            document.getElementById('dynamic-confirm-text').textContent = message;
            
            const yesBtn = document.getElementById('dynamic-confirm-yes');
            const noBtn = document.getElementById('dynamic-confirm-no');
            
            yesBtn.textContent = yesText;
            noBtn.textContent = noText;
            
            const newYesBtn = yesBtn.cloneNode(true);
            const newNoBtn = noBtn.cloneNode(true);
            yesBtn.parentNode.replaceChild(newYesBtn, yesBtn);
            noBtn.parentNode.replaceChild(newNoBtn, noBtn);
            
            newYesBtn.addEventListener('click', () => {
                overlay.classList.remove('active');
                onConfirm();
            });
            
            newNoBtn.addEventListener('click', () => {
                overlay.classList.remove('active');
            });
            
            setTimeout(() => overlay.classList.add('active'), 10);
        }
        function submitExam() {
            if (!quizForm) return;
            const reviewQuestionIds = [];
            gridBtns.forEach((btn, idx) => {
                if (btn.classList.contains('btn-review')) {
                    const slide = document.getElementById(`slide-${idx}`);
                    if (slide) {
                        const qId = slide.getAttribute('data-q-id');
                        if (qId) reviewQuestionIds.push(qId);
                    }
                }
            });
            const reviewInput = document.getElementById('review-questions-input');
            if (reviewInput) {
                reviewInput.value = reviewQuestionIds.join(',');
            }
            quizForm.submit();
        }

        if (submitBtn) {
            submitBtn.addEventListener('click', () => {
                showCustomConfirm(
                    "Submit Exam?",
                    "Are you sure you want to submit your exam?",
                    '<i class="fa-solid fa-paper-plane"></i>',
                    "Yes, Submit",
                    "Cancel",
                    () => {
                        clearAllTimers();
                        submitExam();
                    }
                );
            });
        }
        
        const finalSubmitBtn = document.getElementById('final-submit-btn');
        if (finalSubmitBtn) {
            finalSubmitBtn.addEventListener('click', () => {
                showCustomConfirm(
                    "Finalize Submission?",
                    "Are you sure you want to finalize and submit your exam?",
                    '<i class="fa-solid fa-circle-check"></i>',
                    "Yes, Submit",
                    "Cancel",
                    () => {
                        clearAllTimers();
                        submitExam();
                    }
                );
            });
        }
        
        const markReviewBtn = document.getElementById('mark-review-btn');
        const clearRespBtn = document.getElementById('clear-response-btn');
        const resetConfirmModal = document.getElementById('reset-confirm-modal');
        const confirmResetYes = document.getElementById('confirm-reset-yes-btn');
        const confirmResetNo = document.getElementById('confirm-reset-no-btn');
        
        if (markReviewBtn) {
            markReviewBtn.addEventListener('click', function() {
                const gridBtn = document.getElementById(`grid-btn-${currentSlide}`);
                if (gridBtn) {
                    if (gridBtn.classList.contains('btn-review')) {
                        // Toggle off if already marked for review
                        gridBtn.classList.remove('btn-review');
                        // Check if it has an answer to revert to answered state, else unanswered
                        const parentSlide = document.getElementById(`slide-${currentSlide}`);
                        let hasAnswer = false;
                        if (parentSlide) {
                            const checkedRadio = parentSlide.querySelector('input[type="radio"]:checked');
                            if (checkedRadio) hasAnswer = true;
                        }
                        if (hasAnswer) {
                            gridBtn.classList.add('btn-answered');
                        } else {
                            gridBtn.classList.add('btn-unanswered');
                        }
                    } else {
                        // Toggle on
                        gridBtn.classList.remove('btn-unanswered', 'btn-answered');
                        gridBtn.classList.add('btn-review');
                    }
                    updateStats();
                }
            });
        }
        
        if (clearRespBtn) {
            clearRespBtn.addEventListener('click', function() {
                showCustomConfirm(
                    "Clear Response?",
                    "Are you sure you want to clear your answer for this question?",
                    '<i class="fa-solid fa-eraser"></i>',
                    "Yes, Clear",
                    "Cancel",
                    () => {
                        const parentSlide = document.getElementById(`slide-${currentSlide}`);
                        if (parentSlide) {
                            parentSlide.querySelectorAll('.option-item').forEach(opt => {
                                opt.classList.remove('selected');
                                opt.style.borderColor = 'transparent';
                                const radio = opt.querySelector('input[type="radio"]');
                                if (radio) radio.checked = false;
                            });
                        }
                        const gridBtn = document.getElementById(`grid-btn-${currentSlide}`);
                        if (gridBtn) {
                            gridBtn.classList.remove('btn-review', 'btn-answered');
                            gridBtn.classList.add('btn-unanswered');
                            updateStats();
                        }
                    }
                );
            });
        }
        
        function updateStats() {
            let answeredCount = 0;
            let reviewCount = 0;
            let unansweredCount = 0;

            gridBtns.forEach(btn => {
                if (btn.classList.contains('btn-review')) {
                    reviewCount++;
                } else if (btn.classList.contains('btn-answered')) {
                    answeredCount++;
                } else {
                    unansweredCount++;
                }
            });

            const pillAns = document.getElementById('pill-answered-val');
            const pillRev = document.getElementById('pill-review-val');
            const pillUnans = document.getElementById('pill-unanswered-val');
            
            if (pillAns) pillAns.textContent = answeredCount;
            if (pillRev) pillRev.textContent = reviewCount;
            if (pillUnans) pillUnans.textContent = unansweredCount;

            const answeredPct = totalSlides > 0 ? (answeredCount / totalSlides) * 100 : 0;
            const reviewPct = totalSlides > 0 ? (reviewCount / totalSlides) * 100 : 0;
            const unansweredPct = totalSlides > 0 ? (unansweredCount / totalSlides) * 100 : 0;

            const progAns = document.getElementById('progress-segment-answered');
            const progRev = document.getElementById('progress-segment-review');
            const progUnans = document.getElementById('progress-segment-unanswered');

            if (progAns) progAns.style.width = `${answeredPct}%`;
            if (progRev) progRev.style.width = `${reviewPct}%`;
            if (progUnans) progUnans.style.width = `${unansweredPct}%`;

            // Update individual section progress percentages on tabs
            if (window.sectionsData && validSections.length > 0) {
                validSections.forEach(sec => {
                    if (sec.q_indices && sec.q_indices.length > 0) {
                        let secAnswered = 0;
                        sec.q_indices.forEach(idx => {
                            const slide = document.getElementById(`slide-${idx}`);
                            if (slide && slide.querySelector('input[type="radio"]:checked')) {
                                secAnswered++;
                            }
                        });
                        const secPct = Math.round((secAnswered / sec.q_indices.length) * 100);
                        const secProgSpan = document.getElementById(`sec-progress-${sec.id}`);
                        if (secProgSpan) {
                            secProgSpan.textContent = `${secPct}%`;
                            if (secPct >= 75) {
                                secProgSpan.style.background = 'rgba(16, 185, 129, 0.15)';
                                secProgSpan.style.color = '#059669';
                            } else if (secPct > 0) {
                                secProgSpan.style.background = 'rgba(59, 130, 246, 0.15)';
                                secProgSpan.style.color = '#2563eb';
                            } else {
                                secProgSpan.style.background = 'rgba(0,0,0,0.05)';
                                secProgSpan.style.color = 'inherit';
                            }
                        }
                    }
                });
            }
        }

        const optionItems = document.querySelectorAll('.option-item');
        optionItems.forEach(item => {
            item.addEventListener('click', function () {
                const parentSlide = this.closest('.question-slide');
                parentSlide.querySelectorAll('.option-item').forEach(opt => {
                    opt.classList.remove('selected');
                    opt.style.borderColor = 'transparent';
                });
                this.classList.add('selected');
                this.style.borderColor = 'var(--primary-orange)';
                const radio = this.querySelector('input[type="radio"]');
                if (radio) {
                    radio.checked = true;
                }
                
                const gridBtn = document.getElementById(`grid-btn-${currentSlide}`);
                if (gridBtn) {
                    gridBtn.classList.remove('btn-unanswered', 'btn-review');
                    gridBtn.classList.add('btn-answered');
                }
                updateStats();
            });
        });

        function showSlide(index) {
            const modeSelect = document.getElementById('questions-mode-select');
            const isAllMode = modeSelect && modeSelect.value === 'all';

            const qPalette = document.getElementById('question-palette-box');
            if (qPalette) {
                qPalette.style.display = isAllMode ? 'none' : 'block';
            }

            slides.forEach((slide, idx) => {
                if (isAllMode) {
                    if (currentSectionQIndices && currentSectionQIndices.length > 0) {
                        slide.style.display = currentSectionQIndices.includes(idx) ? 'block' : 'none';
                    } else {
                        slide.style.display = 'block';
                    }
                } else {
                    if (idx === index) {
                        slide.style.display = 'block';
                    } else {
                        slide.style.display = 'none';
                    }
                }
            });

            currentSlide = index;
            const currentQSpans = document.querySelectorAll('.current-idx');
            const totalQSpans = document.querySelectorAll('.total-q-count');
            
            let displayIndex = currentSlide + 1;
            let displayTotal = totalSlides;
            
            if (window.sectionsData && window.sectionsData.length > 0 && validSections.length > 0) {
                const secRelativeIdx = currentSectionQIndices.indexOf(currentSlide);
                if (secRelativeIdx !== -1) {
                    displayIndex = secRelativeIdx + 1;
                    displayTotal = currentSectionQIndices.length;
                }
            }

            currentQSpans.forEach(span => {
                span.textContent = displayIndex;
            });
            if (totalQSpans) {
                totalQSpans.forEach(span => {
                    span.textContent = displayTotal;
                });
            }

            if (isAllMode) {
                if (prevBtn) {
                    prevBtn.style.display = (validSections.length > 0 && currentSectionIndex > 0) ? 'inline-block' : 'none';
                    if (validSections.length === 0) prevBtn.style.display = 'none';
                }

                if (nextBtn && submitBtn) {
                    let isLastSection = true;
                    if (window.sectionsData && window.sectionsData.length > 0 && validSections.length > 0) {
                        const lastSection = validSections[validSections.length - 1];
                        isLastSection = currentSectionIndex === validSections.indexOf(lastSection);
                    }
                    
                    const finalSubmitBtn = document.getElementById('final-submit-btn');

                    if (isLastSection) {
                        nextBtn.style.display = 'none';
                        submitBtn.style.display = 'inline-block';
                        if (finalSubmitBtn) finalSubmitBtn.style.display = 'flex';
                    } else {
                        nextBtn.style.display = 'inline-block';
                        submitBtn.style.display = 'none';
                        if (finalSubmitBtn) finalSubmitBtn.style.display = 'none';
                    }
                }
            } else {
                if (prevBtn) {
                    prevBtn.style.display = currentSlide === 0 ? 'none' : 'inline-block';
                }

                if (nextBtn && submitBtn) {
                    let isLastVisible = true;
                    if (window.sectionsData && window.sectionsData.length > 0 && validSections.length > 0) {
                        const lastSection = validSections[validSections.length - 1];
                        const maxIdx = Math.max(...lastSection.q_indices);
                        isLastVisible = currentSlide === maxIdx;
                    } else {
                        isLastVisible = currentSlide === totalSlides - 1;
                    }

                    const finalSubmitBtn = document.getElementById('final-submit-btn');

                    if (isLastVisible) {
                        nextBtn.style.display = 'none';
                        submitBtn.style.display = 'inline-block';
                        if (finalSubmitBtn) finalSubmitBtn.style.display = 'flex';
                    } else {
                        nextBtn.style.display = 'inline-block';
                        submitBtn.style.display = 'none';
                        if (finalSubmitBtn) finalSubmitBtn.style.display = 'none';
                    }
                }
            }

            gridBtns.forEach(btn => btn.classList.remove('btn-active'));
            const activeGridBtn = document.getElementById(`grid-btn-${currentSlide}`);
            if (activeGridBtn) {
                activeGridBtn.classList.add('btn-active');
            }
        }

        gridBtns.forEach((btn, idx) => {
            btn.addEventListener('click', function () {
                // Disable jumping to questions outside the current section via grid buttons
                let targetSecIndex = -1;
                if (validSections.length > 0) {
                    targetSecIndex = validSections.findIndex(s => s.q_indices.includes(idx));
                }
                
                if (targetSecIndex !== -1 && targetSecIndex !== currentSectionIndex) {
                    // Do nothing - user cannot jump to other sections via grid
                    return;
                } else {
                    showSlide(idx);
                }
            });
        });

        if (prevBtn) {
            prevBtn.addEventListener('click', function () {
                const modeSelect = document.getElementById('questions-mode-select');
                const isAllMode = modeSelect && modeSelect.value === 'all';

                if (isAllMode) {
                    // Previous section navigation is disabled in All mode
                    return;
                } else {
                    let prevIdx = currentSlide - 1;
                    if (prevIdx >= 0) {
                        let targetSecIndex = -1;
                        if (validSections.length > 0) {
                            targetSecIndex = validSections.findIndex(s => s.q_indices.includes(prevIdx));
                        }
                        if (targetSecIndex !== -1 && targetSecIndex !== currentSectionIndex) {
                            // Prevent going back to a previous section
                            return;
                        } else {
                            showSlide(prevIdx);
                        }
                    }
                }
            });
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', function () {
                const modeSelect = document.getElementById('questions-mode-select');
                const isAllMode = modeSelect && modeSelect.value === 'all';

                if (isAllMode) {
                    if (validSections.length > 0 && currentSectionIndex < validSections.length - 1) {
                        if (!isCurrentSectionValid()) {
                            alert("You must answer at least 75% of the questions in this section before moving to the next one.");
                            return;
                        }
                        const targetSecIndex = currentSectionIndex + 1;
                        const nextIdx = validSections[targetSecIndex].q_indices[0];
                        const nextSecTitle = validSections[targetSecIndex].title || validSections[targetSecIndex].name || "next";
                        showCustomConfirm(
                            "Section Complete", 
                            `Can you start next "${nextSecTitle}" section?`,
                            '<i class="fa-solid fa-forward-step"></i>',
                            'Start Section',
                            'Cancel',
                            () => {
                                if (sectionTimerInterval) clearInterval(sectionTimerInterval);
                                activateSection(targetSecIndex, nextIdx);
                            }
                        );
                    }
                } else {
                    let nextIdx = currentSlide + 1;
                    if (nextIdx < totalSlides) {
                        let targetSecIndex = -1;
                        if (validSections.length > 0) {
                            targetSecIndex = validSections.findIndex(s => s.q_indices.includes(nextIdx));
                        }
                        if (targetSecIndex !== -1 && targetSecIndex !== currentSectionIndex) {
                            if (!isCurrentSectionValid()) {
                                alert("You must answer at least 75% of the questions in this section before moving to the next one.");
                                return;
                            }
                            const nextSecTitle = validSections[targetSecIndex].title || validSections[targetSecIndex].name || "next";
                            showCustomConfirm(
                                "Section Complete", 
                                `Can you start next "${nextSecTitle}" section?`,
                                '<i class="fa-solid fa-forward-step"></i>',
                                'Start Section',
                                'Cancel',
                                () => {
                                    if (sectionTimerInterval) clearInterval(sectionTimerInterval);
                                    activateSection(targetSecIndex, nextIdx);
                                }
                            );
                        } else {
                            showSlide(nextIdx);
                        }
                    }
                }
            });
        }

        const modeSelectEl = document.getElementById('questions-mode-select');
        if (modeSelectEl) {
            modeSelectEl.addEventListener('change', function () {
                showSlide(currentSlide);
            });
        }

        // --- Strict Sections & Timer Logic ---
        let currentSectionQIndices = [];
        let currentSectionIndex = 0;
        let validSections = [];
        let sectionTimerInterval = null;

        if (window.sectionsData && window.sectionsData.length > 0) {
            validSections = window.sectionsData.filter(s => s.q_indices.length > 0);
        }

        const timerContainer = document.getElementById('quiz-timer-container');
        const timerValText = document.getElementById('timer-val');
        const timerBarFill = document.getElementById('timer-bar-fill');
        const attemptId = timerContainer ? (timerContainer.dataset.attemptId || timerContainer.dataset.quizId || 'demo_mode') : 'demo_mode';

        // For demo exams, we don't want to load timers from previous abandoned sessions
        if (attemptId === 'demo_mode') {
            if (window.sectionsData) {
                window.sectionsData.forEach(sec => {
                    localStorage.removeItem(`timer_timeLeft_demo_mode_sec_${sec.id}`);
                });
            }
            localStorage.removeItem(`timer_timeLeft_demo_mode`);
        }

        function isCurrentSectionValid() {
            if (validSections.length === 0) return true;
            const qIndices = currentSectionQIndices;
            if (qIndices.length === 0) return true;
            
            let answered = 0;
            qIndices.forEach(idx => {
                const parentSlide = document.getElementById(`slide-${idx}`);
                if (parentSlide) {
                    const checkedRadio = parentSlide.querySelector('input[type="radio"]:checked');
                    if (checkedRadio) answered++;
                }
            });
            
            return (answered / qIndices.length) >= 0.75;
        }

        // Setup tab clicking (Locked for forward-only progression)
        const sectionTabs = document.querySelectorAll('.section-tab-btn');
        sectionTabs.forEach((tab) => {
            tab.style.pointerEvents = 'none'; // Visually disable clicking
            tab.addEventListener('click', function(e) {
                e.preventDefault();
                // Navigation disabled
            });
        });
        
        function activateSection(secIndex, targetSlideIndex = null) {
            if (secIndex >= validSections.length) {
                alert("You have completed all sections. Submitting your answers now...");
                clearAllTimers();
                submitExam();
                return;
            }
            
            const secData = validSections[secIndex];
            currentSectionIndex = secIndex;
            currentSectionQIndices = secData.q_indices;
            
            // Update tabs UI
            const tabs = document.querySelectorAll('.section-tab-btn');
            tabs.forEach(t => {
                t.style.borderColor = 'var(--border-color)';
                t.style.color = 'var(--text-muted)';
                t.style.background = 'var(--card-bg)';
                t.style.opacity = '0.5';
            });
            
            const activeTab = document.querySelector(`.section-tab-btn[data-sec-id="${secData.id}"]`);
            if (activeTab) {
                activeTab.style.borderColor = 'var(--primary-orange)';
                activeTab.style.color = 'var(--primary-orange)';
                activeTab.style.background = 'rgba(255,107,0,0.05)';
                activeTab.style.opacity = '1';
            }
            
            // Hide/show grid buttons and re-number them for the section
            gridBtns.forEach((btn, idx) => {
                const secRelativeIdx = currentSectionQIndices.indexOf(idx);
                if (secRelativeIdx !== -1) {
                    btn.style.display = 'flex';
                    btn.textContent = secRelativeIdx + 1;
                } else {
                    btn.style.display = 'none';
                }
            });
            
            // Hide/show slides
            slides.forEach((slide, idx) => {
                if (currentSectionQIndices.includes(idx)) {
                    slide.classList.add('active-section-slide');
                } else {
                    slide.classList.remove('active-section-slide');
                    slide.style.display = 'none';
                }
            });

            // Go to target question or first question in this section
            if (targetSlideIndex !== null) {
                showSlide(targetSlideIndex);
            } else if (currentSectionQIndices.length > 0) {
                showSlide(currentSectionQIndices[0]);
            }
            updateStats();
            
            // Setup Timer for this section
            if (sectionTimerInterval) clearInterval(sectionTimerInterval);
            if (timerContainer) {
                const timeLimit = parseInt(secData.time_limit, 10);
                if (timeLimit > 0) {
                    timerContainer.style.display = 'flex';
                    if (timerBarFill) timerBarFill.parentElement.style.display = 'block';
                    
                    const storageKey = `timer_timeLeft_${attemptId}_sec_${secData.id}`;
                    let timeLeft = timeLimit;
                    const cachedTime = localStorage.getItem(storageKey);
                    if (cachedTime !== null) {
                        timeLeft = parseInt(cachedTime, 10);
                    }
                    
                    function updateTimerDisplay() {
                        const minutes = Math.floor(timeLeft / 60);
                        const seconds = timeLeft % 60;
                        if (timerValText) timerValText.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                        localStorage.setItem(storageKey, timeLeft);
                        
                        if (timerBarFill) {
                            const pct = (timeLeft / timeLimit) * 100;
                            timerBarFill.style.width = `${pct}%`;
                            if (pct <= 20) {
                                timerBarFill.style.backgroundColor = '#FF1744';
                                timerContainer.style.color = '#FF1744';
                            } else {
                                timerBarFill.style.backgroundColor = 'var(--primary-orange)';
                                timerContainer.style.color = 'var(--primary-orange)';
                            }
                        }
                    }
                    
                    updateTimerDisplay();
                    sectionTimerInterval = setInterval(() => {
                        timeLeft--;
                        if (timeLeft <= 0) {
                            clearInterval(sectionTimerInterval);
                            localStorage.removeItem(storageKey);
                            alert(`Time is up for section: ${secData.title}. Advancing to next section...`);
                            activateSection(currentSectionIndex + 1);
                        } else {
                            updateTimerDisplay();
                        }
                    }, 1000);
                } else {
                    // No time limit for this section
                    timerContainer.style.display = 'none';
                    if (timerBarFill) timerBarFill.parentElement.style.display = 'none';
                }
            }
        }

        // Initialize sections or fallback to general logic
        if (validSections.length > 0) {
            activateSection(0);
        } else {
            // General quiz logic (no sections)
            if (totalSlides > 0) {
                showSlide(0);
                updateStats();
            }
            
            // Standard Timer Logic
            if (timerContainer) {
                const timeLimit = parseInt(timerContainer.dataset.timeLimit, 10) * 60; // Multiply by 60 to convert minutes to seconds
                if (timeLimit > 0) {
                    timerContainer.style.display = 'flex';
                    if (timerBarFill) timerBarFill.parentElement.style.display = 'block';

                    const storageKey = `timer_timeLeft_${attemptId}`;
                    let timeLeft = timeLimit;
                    const cachedTime = localStorage.getItem(storageKey);
                    if (cachedTime !== null) timeLeft = parseInt(cachedTime, 10);
                    
                    sectionTimerInterval = setInterval(() => {
                        timeLeft--;
                        const minutes = Math.floor(timeLeft / 60);
                        const seconds = timeLeft % 60;
                        if (timerValText) timerValText.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                        localStorage.setItem(storageKey, timeLeft);
                        
                        if (timerBarFill) {
                            const pct = (timeLeft / timeLimit) * 100;
                            timerBarFill.style.width = `${pct}%`;
                            if (pct <= 20) {
                                timerBarFill.style.backgroundColor = '#FF1744';
                                timerContainer.style.color = '#FF1744';
                            }
                        }
                        
                        if (timeLeft <= 0) {
                            clearInterval(sectionTimerInterval);
                            localStorage.removeItem(storageKey);
                            alert("Time is up! Submitting your answers now...");
                            submitExam();
                        }
                    }, 1000);
                }
            }
        }
    }

    // --- Dashboard Performance Chart ---
    const chartCanvas = document.getElementById('dashboard-performance-chart');
    const chartDataScript = document.getElementById('dashboardChartData');
    if (chartCanvas && chartDataScript && typeof Chart !== 'undefined') {
        const rawChartData = JSON.parse(chartDataScript.textContent || '[]');
        const labels = rawChartData.map(point => point.date);
        const scores = rawChartData.map(point => point.percentage);

        new Chart(chartCanvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Exam score',
                    data: scores,
                    backgroundColor: 'rgba(255, 107, 0, 0.15)',
                    borderColor: 'rgba(255, 107, 0, 0.95)',
                    borderWidth: 3,
                    pointRadius: 5,
                    pointBackgroundColor: 'rgba(255, 107, 0, 0.95)',
                    tension: 0.35,
                    fill: true,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: 'rgba(255,255,255,0.08)'
                        },
                        ticks: {
                            color: 'rgba(255,255,255,0.75)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255,255,255,0.08)'
                        },
                        ticks: {
                            color: 'rgba(255,255,255,0.75)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return `${context.parsed.y}%`;
                            }
                        }
                    }
                }
            }
        });
    }

    // --- Quiz Overview Modal Dialog ---
    const quizCards = document.querySelectorAll('.quiz-card');
    const modal = document.getElementById('quiz-overview-modal');
    const closeBtn = document.getElementById('close-overview-modal');
    const cancelBtn = document.getElementById('modal-cancel-btn');

    if (modal) {
        const modalTitle = document.getElementById('modal-quiz-title');
        const modalDesc = document.getElementById('modal-quiz-desc');
        const modalSubject = document.getElementById('modal-quiz-subject');
        const modalCategory = document.getElementById('modal-quiz-category');
        const modalDifficulty = document.getElementById('modal-quiz-difficulty');
        const modalQuestions = document.getElementById('modal-quiz-questions');
        const modalPass = document.getElementById('modal-quiz-pass');
        const modalDeadline = document.getElementById('modal-quiz-deadline');
        const modalStartBtn = document.getElementById('modal-start-quiz-btn');

        function openModal(card) {
            const title = card.dataset.title;
            const desc = card.dataset.desc;
            const subject = card.dataset.subject;
            const category = card.dataset.category;
            const difficulty = card.dataset.difficulty;
            const questions = card.dataset.questions;
            const pass = card.dataset.pass;
            const deadline = card.dataset.deadline;
            const playUrl = card.dataset.playUrl;

            modalTitle.textContent = title;
            modalDesc.textContent = desc || "No description provided.";
            modalSubject.textContent = subject || "-";
            modalCategory.textContent = category || "-";
            modalDifficulty.textContent = difficulty || "-";
            modalQuestions.textContent = questions || "0";
            modalPass.textContent = pass ? `${pass}%` : "-";
            modalDeadline.textContent = deadline || "No deadline";
            modalStartBtn.setAttribute('href', playUrl);

            modal.classList.add('active');
        }

        function closeModal() {
            modal.classList.remove('active');
        }

        quizCards.forEach(card => {
            // Bind click to the entire card area
            card.addEventListener('click', function (e) {
                // If they clicked the start button inside the card, prevent direct navigation and open the modal instead
                if (e.target.closest('.quiz-card-start-btn')) {
                    e.preventDefault();
                }
                openModal(this);
            });
        });

        if (closeBtn) closeBtn.addEventListener('click', closeModal);
        if (cancelBtn) cancelBtn.addEventListener('click', closeModal);

        modal.addEventListener('click', function (e) {
            if (e.target === modal) {
                closeModal();
            }
        });
    }
});
