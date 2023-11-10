import sys
import datetime
import cv2
import sqlite3
import mediapipe as mp
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QFileDialog, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt5.QtGui import QImage
from result import Results

# Initialize MediaPipe components
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_face_mesh = mp.solutions.face_mesh


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("easy_eyes_des.ui", self)
        self.initUI()

    def initUI(self):
        self.setCentralWidget(self.centralwidget)
        self.pushButton.clicked.connect(self.open_image)
        # Создаем экземпляр класса Results
        self.results_window = Results()
        # Создаем кнопку для открытия окна с результатами
        self.show_results_button.clicked.connect(self.show_results_window)

    def show_results_window(self):
        # Открываем окно с результатами
        self.results_window.show()

    def open_image(self):
        self.file_path = QFileDialog.getOpenFileName(
            self, 'Выбрать картинку', '',
            'Картинка (*.jpg);;Картинка (*.png);;Все файлы (*)')[0]
        if self.file_path:
            con = sqlite3.connect("Eyes_data.sqlite")
            cur = con.cursor()

            self.process_image(self.file_path)
            self.eye_color = self.calculate_eye_color(self.annotated_image, self.coords)
            self.last_result = cur.execute("SELECT * FROM result WHERE id=(SELECT MAX(id) FROM result)").fetchall()
            self.last_color = self.last_result[0][2].replace('[', '').replace(']', '').split(', ')
            self.insert(str(self.eye_color))
            self.comparing(self.eye_color, self.last_color)
            self.eye_color_label_2.setText(f"Программа рассчитала средний цвет глаз {self.eye_color}")
            con.close()
        else:
            self.label.setText("Фото не обнаружено")

    def draw_red_pixels(self, image, coordinates):
        for coord in coordinates[:2]:
            x, y = int(coord.x * image.shape[1]), int(coord.y * image.shape[0])
            cv2.circle(image, (x + 6, y + 4), 2, (0, 0, 255), -1)
        for coord in coordinates[2:]:
            x, y = int(coord.x * image.shape[1]), int(coord.y * image.shape[0])
            cv2.circle(image, (x - 6, y + 2), 2, (0, 0, 255), -1)

    def calculate_eye_color(self, image, coordinates):
        eye_colors = []

        for coord in coordinates[:2]:
            x, y = int(coord.x * image.shape[1]), int(coord.y * image.shape[0])
            eye_color = image[y + 6, x + 4]
            eye_colors.append(eye_color)

        for coord in coordinates[2:]:
            x, y = int(coord.x * image.shape[1]), int(coord.y * image.shape[0])
            eye_color = image[y - 6, x + 2]
            eye_colors.append(eye_color)

        # Если список пуст, вернуть черный цвет
        if not eye_colors:
            return [0, 0, 0]

        avg_eye_color = np.mean(eye_colors, axis=0)
        return avg_eye_color.tolist()

    def insert(self, colour):
        connection = sqlite3.connect("Eyes_data.sqlite")
        cursor = connection.cursor()

        # Получить текущую дату и время
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")

        # Вставить данные в таблицу "result"
        cursor.execute("INSERT INTO result (data, colour) VALUES (?, ?)", (current_date, colour))

        connection.commit()
        connection.close()

    def comparing(self, eye_color, last_color):
        normal = True

        for col in range(len(eye_color)):
            if str(int(eye_color[col]) - 10) > str(last_color[col]) or str(int(eye_color[col]) + 10) < str(
                    last_color[col]):
                normal = False

        if normal:
            self.recom.setText("Можете продолжать работать, проверьтесь через 30 минут и сделайте перерыв")
        else:
            self.recom.setText(
                "Программа зафиксировала резкое изменение цвета пикселей глаз, рекомендуется сделать перерыв")

    def process_image(self, file_path):
        image = cv2.imread(file_path)

        if image is None:
            self.label.setText(
                f"Ошибка: не удалось открыть изображение {self.file_path}. Убедитесь, что путь до фотографии корректен.")
        else:
            with mp_face_mesh.FaceMesh(
                    static_image_mode=True,
                    max_num_faces=2,
                    refine_landmarks=True,
                    min_detection_confidence=0.5) as face_mesh:

                # Process the selected image
                results = face_mesh.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

                # Print and draw face mesh landmarks on the image.
                if not results.multi_face_landmarks:
                    self.label.setText("No face landmarks detected in the selected image.")
                else:
                    self.annotated_image = image.copy()
                    for face_landmarks in results.multi_face_landmarks:
                        mp_drawing.draw_landmarks(
                            image=self.annotated_image,
                            landmark_list=face_landmarks,
                            connections=mp_face_mesh.FACEMESH_RIGHT_EYE,
                            landmark_drawing_spec=None,
                            connection_drawing_spec=mp_drawing_styles.DrawingSpec(color=(0, 255, 0), thickness=1,
                                                                                  circle_radius=2))
                        mp_drawing.draw_landmarks(
                            image=self.annotated_image,
                            landmark_list=face_landmarks,
                            connections=mp_face_mesh.FACEMESH_LEFT_EYE,
                            landmark_drawing_spec=None,
                            connection_drawing_spec=mp_drawing_styles.DrawingSpec(color=(0, 255, 0), thickness=1,
                                                                                  circle_radius=2))
                        mp_drawing.draw_landmarks(
                            image=self.annotated_image,
                            landmark_list=face_landmarks,
                            connections=mp_face_mesh.FACEMESH_IRISES,
                            landmark_drawing_spec=None,
                            connection_drawing_spec=mp_drawing_styles.DrawingSpec(color=(0, 255, 0), thickness=1,
                                                                                  circle_radius=2))
                    self.coords = [results.multi_face_landmarks[0].landmark[469],
                                   results.multi_face_landmarks[0].landmark[474],
                                   results.multi_face_landmarks[0].landmark[471],
                                   results.multi_face_landmarks[0].landmark[476]]

                    self.eye_color = self.calculate_eye_color(self.annotated_image, self.coords)
                    self.draw_red_pixels(self.annotated_image, self.coords)
                    # Display the annotated image
                    cv2.imshow("annotated_image.png", self.annotated_image)
                    self.label.setText("Ориентиры лица обнаружены")
                    return self.eye_color


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

    # # For webcam input:
# drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)
# cap = cv2.VideoCapture(0)
# with mp_face_mesh.FaceMesh(
#     max_num_faces=1,
#     refine_landmarks=True,
#     min_detection_confidence=0.5,
#     min_tracking_confidence=0.5) as face_mesh:
#   while cap.isOpened():
#     success, image = cap.read()
#     if not success:
#       print("Ignoring empty camera frame.")
#       # If loading a video, use 'break' instead of 'continue'.
#       continue
#
#     # To improve performance, optionally mark the image as not writeable to
#     # pass by reference.
#     image.flags.writeable = False
#     image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
#     results = face_mesh.process(image)
#
#     # Draw the face mesh annotations on the image.
#     image.flags.writeable = True
#     image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
#     if results.multi_face_landmarks:
#       for face_landmarks in results.multi_face_landmarks:
#         mp_drawing.draw_landmarks(
#             image=image,
#             landmark_list=face_landmarks,
#             connections=mp_face_mesh.FACEMESH_LEFT_EYE,
#             landmark_drawing_spec=None,
#             connection_drawing_spec=mp_drawing_styles.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=2))
#         mp_drawing.draw_landmarks(
#           image=image,
#           landmark_list=face_landmarks,
#           connections=mp_face_mesh.FACEMESH_RIGHT_EYE,
#           landmark_drawing_spec=None,
#           connection_drawing_spec=mp_drawing_styles.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=2))
#         mp_drawing.draw_landmarks(
#             image=image,
#             landmark_list=face_landmarks,
#             connections=mp_face_mesh.FACEMESH_IRISES,
#             landmark_drawing_spec=None,
#             connection_drawing_spec=mp_drawing_styles.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=2))
#     t1 = list(results.multi_face_landmarks[0].landmark)
#     print(t1)
#
#     cv2.imshow('MediaPipe Face Mesh', cv2.flip(image, 1))
#     if cv2.waitKey(5) & 0xFF == 27:
#         break
# cap.release()
