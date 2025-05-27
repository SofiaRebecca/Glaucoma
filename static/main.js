// Main JavaScript for Glaucoma Detection System

// Common test functionality
class TestBase {
    constructor(testName) {
        this.testName = testName;
        this.patientName = localStorage.getItem('patientName') || 'Unknown';
        this.startTime = new Date();
        this.results = {
            correct: 0,
            total: 0,
            responses: []
        };
        this.socket = null;

        this.initializeSocket();
        this.addExitButton();
    }

    initializeSocket() {
        // Connect to main server for result reporting
        this.socket = io();

        this.socket.on('connect', () => {
            console.log('Connected to main server');
        });
    }

    addExitButton() {
        const exitBtn = document.createElement('button');
        exitBtn.className = 'test-exit-btn';
        exitBtn.innerHTML = '<i class="fas fa-times"></i> Exit Test';
        exitBtn.onclick = () => this.exitTest();
        document.body.appendChild(exitBtn);
    }

    exitTest() {
        if (confirm('Are you sure you want to exit this test?')) {
            window.location.href = '/patient';
        }
    }

    recordResponse(correct, responseTime, additionalData = {}) {
        this.results.total++;
        if (correct) {
            this.results.correct++;
        }

        this.results.responses.push({
            correct: correct,
            responseTime: responseTime,
            timestamp: new Date(),
            ...additionalData
        });
    }

    completeTest(additionalResults = {}) {
        const endTime = new Date();
        const duration = Math.round((endTime - this.startTime) / 1000);
        const accuracy = this.results.total > 0 ? 
            Math.round((this.results.correct / this.results.total) * 100) : 0;

        const testData = {
            test_name: this.testName,
            patient_name: this.patientName,
            start_time: this.startTime.toLocaleTimeString(),
            end_time: endTime.toLocaleTimeString(),
            duration: duration,
            total_points: this.results.total,
            correct_points: this.results.correct,
            accuracy: accuracy,
            responses: this.results.responses,
            ...additionalResults
        };

        // Send results to main server
        if (this.socket) {
            this.socket.emit('test_completed', testData);
        }

        // Show results
        this.showResults(testData);
    }

    showResults(data) {
        document.body.innerHTML = `
            <div class="container-fluid min-vh-100 d-flex align-items-center justify-content-center" style="background: #1a1a1a; color: white;">
                <div class="text-center">
                    <div class="mb-4">
                        <i class="fas fa-check-circle fa-4x text-success mb-3"></i>
                        <h2>Test Completed</h2>
                    </div>

                    <div class="card bg-dark border-secondary mx-auto" style="max-width: 500px;">
                        <div class="card-body">
                            <h5 class="card-title">${data.test_name} Results</h5>
                            <hr>
                            <div class="row text-center">
                                <div class="col-4">
                                    <h3 class="text-primary">${data.accuracy}%</h3>
                                    <small>Accuracy</small>
                                </div>
                                <div class="col-4">
                                    <h3 class="text-info">${data.duration}s</h3>
                                    <small>Duration</small>
                                </div>
                                <div class="col-4">
                                    <h3 class="text-success">${data.correct_points}/${data.total_points}</h3>
                                    <small>Score</small>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="mt-4">
                        <button class="btn btn-primary btn-lg me-3" onclick="window.location.href='/patient'">
                            <i class="fas fa-arrow-left me-2"></i>
                            Back to Tests
                        </button>
                        <button class="btn btn-success btn-lg" onclick="location.reload()">
                            <i class="fas fa-redo me-2"></i>
                            Retake Test
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    addProgressBar() {
        const progressContainer = document.createElement('div');
        progressContainer.className = 'test-progress';

        const progressBar = document.createElement('div');
        progressBar.className = 'test-progress-bar';
        progressBar.id = 'test-progress-bar';
        progressBar.style.width = '0%';

        progressContainer.appendChild(progressBar);
        document.body.appendChild(progressContainer);
    }

    updateProgress(percentage) {
        const progressBar = document.getElementById('test-progress-bar');
        if (progressBar) {
            progressBar.style.width = percentage + '%';
        }
    }

    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
        } else if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }
}

// Handle keyboard shortcuts
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        if (document.fullscreenElement) {
            document.exitFullscreen();
        } else if (typeof exitTest === 'function') {
            exitTest();
        }
    } else if (e.key === 'F11') {
        e.preventDefault();
        if (test && typeof test.toggleFullscreen === 'function') {
            test.toggleFullscreen();
        }
    }
});

// Utility functions
function getRandomPosition(container, elementSize = 20) {
    const maxX = container.offsetWidth - elementSize;
    const maxY = container.offsetHeight - elementSize;

    return {
        x: Math.random() * maxX,
        y: Math.random() * maxY
    };
}

function measureResponseTime(startTime) {
    return Date.now() - startTime;
}

function createLanguageToggle(englishCallback, kannadaCallback) {
    const toggle = document.createElement('div');
    toggle.className = 'language-toggle';
    toggle.innerHTML = `
        <div class="btn-group" role="group">
            <button type="button" class="btn btn-outline-light btn-sm" id="english-btn">English</button>
            <button type="button" class="btn btn-outline-light btn-sm" id="kannada-btn">ಕನ್ನಡ</button>
        </div>
    `;

    document.body.appendChild(toggle);

    document.getElementById('english-btn').onclick = () => {
        document.getElementById('english-btn').className = 'btn btn-light btn-sm';
        document.getElementById('kannada-btn').className = 'btn btn-outline-light btn-sm';
        englishCallback();
    };

    document.getElementById('kannada-btn').onclick = () => {
        document.getElementById('kannada-btn').className = 'btn btn-light btn-sm';
        document.getElementById('english-btn').className = 'btn btn-outline-light btn-sm';
        kannadaCallback();
    };
}

// Export for use in test modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TestBase, getRandomPosition, measureResponseTime, createLanguageToggle };
}

// Make available globally
window.TestBase = TestBase;
window.getRandomPosition = getRandomPosition;
window.measureResponseTime = measureResponseTime;
window.createLanguageToggle = createLanguageToggle;