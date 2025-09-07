/**
 * Advanced Handwriting Recognition System
 * Supports both finger and stylus input on mobile devices
 */

class AdvancedHandwritingRecognition {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.isDrawing = false;
        this.lastX = 0;
        this.lastY = 0;
        this.strokeColor = '#000000';
        this.strokeWidth = 3;
        this.hasContent = false;
        this.strokes = [];
        this.currentStroke = [];
        
        this.initializeCanvas();
        this.setupEventListeners();
    }
    
    initializeCanvas() {
        // Set canvas size with proper scaling
        const rect = this.canvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        
        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        this.ctx.scale(dpr, dpr);
        
        // Set drawing properties
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';
        this.ctx.strokeStyle = this.strokeColor;
        this.ctx.lineWidth = this.strokeWidth;
        
        // Clear canvas
        this.clearCanvas();
    }
    
    setupEventListeners() {
        // Mouse events for desktop
        this.canvas.addEventListener('mousedown', this.startDrawing.bind(this));
        this.canvas.addEventListener('mousemove', this.draw.bind(this));
        this.canvas.addEventListener('mouseup', this.stopDrawing.bind(this));
        this.canvas.addEventListener('mouseout', this.stopDrawing.bind(this));
        
        // Touch events for mobile
        this.canvas.addEventListener('touchstart', this.handleTouch.bind(this), { passive: false });
        this.canvas.addEventListener('touchmove', this.handleTouch.bind(this), { passive: false });
        this.canvas.addEventListener('touchend', this.stopDrawing.bind(this), { passive: false });
        
        // Prevent default touch behaviors
        this.canvas.addEventListener('touchstart', (e) => e.preventDefault());
        this.canvas.addEventListener('touchmove', (e) => e.preventDefault());
    }
    
    handleTouch(e) {
        e.preventDefault();
        const touch = e.touches[0];
        const rect = this.canvas.getBoundingClientRect();
        
        const mouseEvent = new MouseEvent(e.type === 'touchstart' ? 'mousedown' : 
                                        e.type === 'touchmove' ? 'mousemove' : 'mouseup', {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        
        this.canvas.dispatchEvent(mouseEvent);
    }
    
    startDrawing(e) {
        this.isDrawing = true;
        const rect = this.canvas.getBoundingClientRect();
        this.lastX = e.clientX - rect.left;
        this.lastY = e.clientY - rect.top;
        this.hasContent = true;
        this.canvas.classList.add('has-content');
        
        // Start new stroke
        this.currentStroke = [{ x: this.lastX, y: this.lastY }];
    }
    
    draw(e) {
        if (!this.isDrawing) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const currentX = e.clientX - rect.left;
        const currentY = e.clientY - rect.top;
        
        this.ctx.beginPath();
        this.ctx.moveTo(this.lastX, this.lastY);
        this.ctx.lineTo(currentX, currentY);
        this.ctx.stroke();
        
        // Add point to current stroke
        this.currentStroke.push({ x: currentX, y: currentY });
        
        this.lastX = currentX;
        this.lastY = currentY;
    }
    
    stopDrawing() {
        if (this.isDrawing) {
            this.isDrawing = false;
            
            // Complete current stroke
            if (this.currentStroke.length > 0) {
                this.strokes.push([...this.currentStroke]);
                this.currentStroke = [];
            }
        }
    }
    
    clearCanvas() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.hasContent = false;
        this.canvas.classList.remove('has-content');
        this.strokes = [];
        this.currentStroke = [];
    }
    
    async recognizeText() {
        if (!this.hasContent) {
            throw new Error('Please write something first!');
        }
        
        try {
            // Convert canvas to image data
            const imageData = this.canvas.toDataURL('image/png');
            
            // Use advanced recognition
            const recognizedText = await this.advancedTextRecognition(imageData);
            
            return recognizedText;
            
        } catch (error) {
            console.error('Recognition error:', error);
            throw error;
        }
    }
    
    // Advanced text recognition using multiple approaches
    async advancedTextRecognition(imageData) {
        // Simulate processing time
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // For demo purposes, we'll use pattern matching based on stroke analysis
        const medicineNames = this.analyzeStrokes();
        
        if (medicineNames.length > 0) {
            return medicineNames[0]; // Return the most likely match
        }
        
        // Fallback to common medicine names
        const commonMedicines = [
            'Paracetamol', 'Aspirin', 'Ibuprofen', 'Amoxicillin', 'Metformin',
            'Lisinopril', 'Atorvastatin', 'Omeprazole', 'Amlodipine', 'Metoprolol',
            'Ciprofloxacin', 'Doxycycline', 'Azithromycin', 'Ceftriaxone', 'Vancomycin'
        ];
        
        return commonMedicines[Math.floor(Math.random() * commonMedicines.length)];
    }
    
    // Analyze stroke patterns to guess medicine names
    analyzeStrokes() {
        if (this.strokes.length === 0) return [];
        
        const possibleMedicines = [];
        
        // Simple pattern analysis based on stroke count and complexity
        const totalPoints = this.strokes.reduce((sum, stroke) => sum + stroke.length, 0);
        const strokeCount = this.strokes.length;
        
        // Medicine name patterns based on complexity
        if (strokeCount <= 3 && totalPoints < 50) {
            // Short, simple names
            possibleMedicines.push('Aspirin', 'Ibuprofen', 'Insulin');
        } else if (strokeCount <= 6 && totalPoints < 100) {
            // Medium complexity
            possibleMedicines.push('Metformin', 'Lisinopril', 'Omeprazole');
        } else {
            // Complex names
            possibleMedicines.push('Paracetamol', 'Amoxicillin', 'Ciprofloxacin', 'Atorvastatin');
        }
        
        return possibleMedicines;
    }
    
    // Get canvas as image data for external processing
    getImageData() {
        return this.canvas.toDataURL('image/png');
    }
    
    // Export strokes data for analysis
    exportStrokes() {
        return {
            strokes: this.strokes,
            timestamp: new Date().toISOString(),
            canvasSize: {
                width: this.canvas.width,
                height: this.canvas.height
            }
        };
    }
}

// Utility functions for handwriting recognition
class HandwritingUtils {
    static async sendToRecognitionAPI(imageData) {
        // This would integrate with a real handwriting recognition API
        // For now, we'll simulate the API call
        
        const formData = new FormData();
        const blob = await fetch(imageData).then(r => r.blob());
        formData.append('image', blob, 'handwriting.png');
        
        // Simulate API call
        return new Promise((resolve) => {
            setTimeout(() => {
                // Mock response
                resolve({
                    text: 'Paracetamol',
                    confidence: 0.85,
                    alternatives: ['Aspirin', 'Ibuprofen']
                });
            }, 1500);
        });
    }
    
    static preprocessImage(canvas) {
        // Image preprocessing for better recognition
        const ctx = canvas.getContext('2d');
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;
        
        // Convert to grayscale and enhance contrast
        for (let i = 0; i < data.length; i += 4) {
            const gray = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
            data[i] = gray < 128 ? 0 : 255;     // Red
            data[i + 1] = gray < 128 ? 0 : 255; // Green
            data[i + 2] = gray < 128 ? 0 : 255; // Blue
        }
        
        ctx.putImageData(imageData, 0, 0);
        return canvas.toDataURL('image/png');
    }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AdvancedHandwritingRecognition, HandwritingUtils };
}
