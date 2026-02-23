import sys
import time
import random
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QThread, Signal
from PySide6.QtUiTools import loadUiType
from transformers import pipeline

EKMAN_EMOTIONS = ['anger', 'disgust', 'fear', 'joy', 'sadness', 'surprise']

EMOTION_MAP = {
    'anger': 'Anger 😡',
    'disgust': 'Disgust 🤢',
    'fear': 'Fear 😨',
    'joy': 'Joy 😀',
    'neutral': 'Neutral 😐',
    'sadness': 'Sadness 😭',
    'surprise': 'Surprise 😲'
}

Ui_MainWindow, QMainWindowBase = loadUiType("emotion_game.ui")

class Classifier(QThread):
    finished = Signal(str)

    def __init__(self, text, classifier):
        super().__init__()
        self.text = text
        self.classifier = classifier

    def run(self):
        result = self.classifier(self.text)[0][0]
        self.finished.emit(result['label'])

class EmotionGame(QMainWindowBase, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.status_label.setText("Loading AI Model...")
        self.text_field.setDisabled(True)

        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_timer_display)

        self.text_field.textChanged.connect(self.on_text_changed)
        self.text_field.returnPressed.connect(self.on_enter_pressed)

        self.load_model()

    def load_model(self):
        self.classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", top_k=1)
        self.reset_game() 

    def reset_game(self):
        self.emotions = random.sample(EKMAN_EMOTIONS, len(EKMAN_EMOTIONS))
        self.current_time = 0.0
        self.penalties = 0.0
        self.is_typing = False
        self.burst_start = 0.0 
        
        self.text_field.setDisabled(False)
        self.text_field.clear()
        self.text_field.setFocus()
        
        self.time_label.setText("00:00:00.00")
        self.update_display()
        self.status_label.setText("Ready! Start typing...")

    def format_time(self, sec):
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        ms = int((sec - int(sec)) * 100)
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:02d}"

    def update_display(self):
        if self.emotions:
            target_display = EMOTION_MAP[self.emotions[0]]
            self.emotion_label.setText(f"Target: {target_display}")
        else:
            final_time = self.current_time + self.penalties
            self.emotion_label.setText("🎉 RUN COMPLETE! 🥳")
            self.time_label.setText(self.format_time(final_time))
            self.status_label.setText(f"{self.penalties}s in penalties. Press ENTER to play again!")

    def on_text_changed(self, text):
        if text and not self.is_typing and self.emotions:
            self.is_typing = True
            self.burst_start = time.time()
            self.ui_timer.start(50)
            self.status_label.setText("Speedrun in progress...")

    def update_timer_display(self):
        if self.is_typing:
            current_burst = time.time() - self.burst_start
            total = self.current_time + current_burst + self.penalties
            self.time_label.setText(self.format_time(total))

    def on_enter_pressed(self):
        if not self.emotions:
            self.reset_game()
            return

        text = self.text_field.text().strip()
        if len(text) <= 3: 
            self.status_label.setText("Input too short...")
            return

        self.is_typing = False
        self.ui_timer.stop()
        self.current_time += (time.time() - self.burst_start)
        
        self.text_field.setDisabled(True)
        self.status_label.setText("Predicting...")

        self.classifAI = Classifier(text, self.classifier)
        self.classifAI.finished.connect(self.predict)
        self.classifAI.start()

    def predict(self, predicted):
        if predicted == self.emotions[0]:
            self.emotions.pop(0)
            self.status_label.setText("✅ Hit!")
        else:
            self.penalties += 2.0
            pred_display = EMOTION_MAP[predicted]
            self.status_label.setText(f"❌ Miss! (+2s) \n AI felt {pred_display}")
            self.time_label.setText(self.format_time(self.current_time + self.penalties))

        self.text_field.setDisabled(False)
        self.text_field.clear()
        self.text_field.setFocus()
        self.update_display()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EmotionGame()
    window.show()
    sys.exit(app.exec())