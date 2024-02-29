import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, UpSampling2D, BatchNormalization
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.optimizers import Adam
import pydicom
from pydicom.pixel_data_handlers.util import apply_voi_lut
import os
from skimage.transform import resize
from sklearn.model_selection import train_test_split

def load_dicom_image(path, img_size=(224, 224)):
    dicom = pydicom.read_file(path)
    data = apply_voi_lut(dicom.pixel_array, dicom)  
    if data.dtype != np.float32:
        data = data.astype(np.float32)
    data = (data - np.min(data)) / (np.max(data) - np.min(data)) 
    data = resize(data, img_size, mode='reflect', anti_aliasing=True)  
    return np.stack((data,)*3, axis=-1)  


def load_dicom_directory(directory, img_size=(224, 224)):
    images = []
    for filename in os.listdir(directory):
        if filename.lower().endswith('.dcm'):
            path = os.path.join(directory, filename)
            images.append(load_dicom_image(path, img_size))
    return np.array(images)


def dicom_generator(X, batch_size=32):
    while True:
        for i in range(0, len(X), batch_size):
            batch_images = X[i:i+batch_size]
            yield batch_images, batch_images  

def create_autoencoder(input_shape=(224, 224, 3)):
    input_img = Input(shape=input_shape)
    x = Conv2D(32, (3, 3), activation='relu', padding='same')(input_img)
    x = MaxPooling2D((2, 2), padding='same')(x)
    x = Conv2D(16, (3, 3), activation='relu', padding='same')(x)
    x = MaxPooling2D((2, 2), padding='same')(x)
    x = Conv2D(16, (3, 3), activation='relu', padding='same')(x)
    x = UpSampling2D((2, 2))(x)
    x = Conv2D(32, (3, 3), activation='relu', padding='same')(x)
    x = UpSampling2D((2, 2))(x)
    decoded = Conv2D(3, (3, 3), activation='sigmoid', padding='same')(x)
    autoencoder = Model(input_img, decoded)
    autoencoder.compile(optimizer=Adam(learning_rate=0.001), loss='binary_crossentropy')
    return autoencoder


def train_autoencoder(directory):
    
    images = load_dicom_directory(directory)
 
    X_train, X_val = train_test_split(images, test_size=0.2, random_state=42)
    
    autoencoder = create_autoencoder()
    autoencoder.summary()
    
    early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
    

    train_gen = dicom_generator(X_train)
    val_gen = dicom_generator(X_val)
    
    history = autoencoder.fit(
        train_gen,
        steps_per_epoch=len(X_train) // 32,
        validation_data=val_gen,
        validation_steps=len(X_val) // 32,
        epochs=50,
        callbacks=[early_stopping]
    )
    
   
    plt.plot(history.history['loss'], label='Training Loss')
    plt.plot(history.history['val_loss'], label='Validation Loss')
    plt.legend()
    plt.show()
    
    return autoencoder

if __name__ == '__main__':
    directory = 'C:/Users/user/Desktop/healthcare/covid_ct_scans'
    model = train_autoencoder(directory)
