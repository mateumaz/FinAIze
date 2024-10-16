import numpy as np
import tensorflow as tf
from sklearn.utils.class_weight import compute_class_weight
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.callbacks import Callback
import pickle
import os
from keras.losses import CategoricalFocalCrossentropy
from functions_v2 import File
from keras.utils import to_categorical
import pandas as pd

from keras.callbacks import EarlyStopping
from sklearn.model_selection import KFold


class CustomEarlyStoppingByAccuracy(Callback):
    def __init__(self, monitor='accuracy', target=0.95, verbose=1):
        super(CustomEarlyStoppingByAccuracy, self).__init__()
        self.monitor = monitor
        self.target = target
        self.verbose = verbose

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        accuracy = logs.get(self.monitor)
        if accuracy is not None and accuracy >= self.target:
            if self.verbose > 0:
                print(f"\nEpoch {epoch + 1}: early stopping - target {self.monitor} reached {self.target * 100:.2f}%")
            self.model.stop_training = True



def model(sequences, labels):
    
    tokenizer = Tokenizer(num_words=100, oov_token='<OOV>')
    tokenizer.fit_on_texts(sequences)
    word_index = tokenizer.word_index

    sequences = tokenizer.texts_to_sequences(sequences)
    padded_sequences = pad_sequences(sequences, maxlen=5)
    labels = np.array(labels)

    # Unikalne klasy
    classes = np.unique(labels)

    model = tf.keras.Sequential([
        tf.keras.layers.Embedding(input_dim=len(word_index) + 1, output_dim=16, input_length=5),
        tf.keras.layers.GlobalAveragePooling1D(),
        tf.keras.layers.Dense(16, activation='relu'),
        tf.keras.layers.Dense(len(classes), activation='softmax')
    ])

    target_accuracy = 0.95
    early_stopping = CustomEarlyStoppingByAccuracy(monitor='accuracy', target=target_accuracy, verbose=1)

    # Obliczanie wag klas
    class_weights = compute_class_weight(class_weight='balanced', classes=classes, y=labels)
    focal_loss = CategoricalFocalCrossentropy(alpha=class_weights)
    labels_one_hot = to_categorical(labels, num_classes=len(classes))
    model.compile(optimizer='adam', loss=focal_loss, metrics=['accuracy'])
    model.fit(padded_sequences, labels_one_hot, epochs=400, verbose=0)
    # w model.fit było na końcu - , callbacks=[early_stopping]

    return model, tokenizer


def save_model_and_tokenizer(model: tf.keras.Sequential, tokenizer: Tokenizer, model_name: str, tokenizer_name: str) -> None:

    directory = os.path.dirname(__file__)
    model_path = directory + '\\' + model_name +  '.keras' #'.h5'
    tokenizer_path = directory + '\\' + tokenizer_name + '.pickle'

    model.save(model_path)

    with open(tokenizer_path, 'wb') as handle:
        pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)


def load_model_and_tokenizer(model_name: str, tokenizer_name: str):

    loaded_model = tf.keras.models.load_model(model_name + '.keras')   #'.h5'
    with open(tokenizer_name + '.pickle', 'rb') as handle:
        loaded_tokenizer = pickle.load(handle)

    return loaded_model, loaded_tokenizer


def predict(model: tf.keras.Sequential, tokenizer: Tokenizer, data: File) -> list[list]:

    sequences = tokenizer.texts_to_sequences(data.exp_seq)
    padded_test_sequences = pad_sequences(sequences, maxlen=5)

    predictions = model.predict(padded_test_sequences)

    # przygotowanie dataframea do zapisu wag do pliku csv --------------------------------------------------------------------------------------------------------
    headers = ['0', '1', '2', '3', '4', '5', '6']
    cat0 = []
    cat1 = []
    cat2 = []
    cat3 = []
    cat4 = []
    cat5 = []
    cat6 = []

    for pre in predictions:
        cat0.append(str(pre[0]).replace('.',','))
        cat1.append(str(pre[1]).replace('.',','))
        cat2.append(str(pre[2]).replace('.',','))
        cat3.append(str(pre[3]).replace('.',','))
        cat4.append(str(pre[4]).replace('.',','))
        cat5.append(str(pre[5]).replace('.',','))
        cat6.append(str(pre[6]).replace('.',','))
    df = pd.DataFrame(columns=headers)
    df['0'] = cat0
    df['1'] = cat1
    df['2'] = cat2
    df['3'] = cat3
    df['4'] = cat4
    df['5'] = cat5
    df['6'] = cat6
    # -----------------------------------------------------------------------------------------------------------------------------------


    predicted_classes = np.argmax(predictions, axis=1)
    predicted_classes = [pred for pred in predicted_classes]

    # Finding uncertain predictions
    # 1st method 
    sorted_predictions = np.sort(predictions, axis=1)[:, ::-1]
    max_values = sorted_predictions[:, 0]
    second_max_values = sorted_predictions[:, 1]
    differences = max_values - second_max_values
    correction_indexes = []
    # for i in range(len(differences)):
    #     if differences[i] < 0.75:
    #         correction_indexes.append(i)

    # 2nd method
    confidences = [max(pred) for pred in predictions]
    percentile = 15
    treshold = np.percentile(confidences, percentile)
    for i in range(len(max_values)):
        if max_values[i] < treshold:
            correction_indexes.append(i)
    print(treshold)

    # zapis do pliku csv --------------------------------------------------------------------------------------------------------------------
    to_correct = [0 for _ in range(len(predicted_classes))]
    for index in correction_indexes:
        to_correct[index] = 1

    df['Real classes'] = None
    df['Predicted'] = predicted_classes
    df['To correct'] = to_correct
    df.to_csv('model_predict_analysis.csv', sep=';', index=False, encoding='utf-8-sig')
    # -----------------------------------------------------------------------------------------------------------------------------------


    return [predicted_classes, correction_indexes]



def train_model(model :tf.keras.Sequential, tokenizer: Tokenizer, data: File) -> None:
    
    kf = KFold(n_splits=5, shuffle = True)  # Podziel dane na 5 części
    X = data.exp_seq 
    y = [data.expences.loc[i,'Labels'] for i in range(len(data.expences))]
    
    tokenizer.fit_on_texts(X)
    word_index = tokenizer.word_index

    X = tokenizer.texts_to_sequences(X)
    X = pad_sequences(X, maxlen=5)
    y = np.array(y)
    classes = np.unique(y)

    old_embedding_weights = model.layers[0].get_weights()[0]
    new_input_dim = len(word_index) + 1  
    new_embedding_layer = tf.keras.layers.Embedding(input_dim=new_input_dim, output_dim=16, input_length=5)

    # Copy existing weights to new embeding layer
    new_embedding_weights = np.zeros((new_input_dim, 16))
    new_embedding_weights[:old_embedding_weights.shape[0], :] = old_embedding_weights
    new_embedding_layer.build((None,))
    new_embedding_layer.set_weights([new_embedding_weights])

    new_model = tf.keras.Sequential([
        new_embedding_layer,
        tf.keras.layers.GlobalAveragePooling1D(),
        tf.keras.layers.Dense(16, activation='relu'),
        tf.keras.layers.Dense(len(classes), activation='softmax')
    ])

    # Copy weights of other layers
    for i in range(1, len(new_model.layers)):
        new_model.layers[i].set_weights(model.layers[i].get_weights())

    for train_index, val_index in kf.split(X):
        X_train, X_val = X[train_index], X[val_index]
        y_train, y_val = y[train_index], y[val_index]

        class_weights = compute_class_weight(class_weight='balanced', classes=classes, y=y_train)
        focal_loss = CategoricalFocalCrossentropy(alpha=class_weights)
        y_train_one_hot = to_categorical(y_train, num_classes=len(classes))
        y_val_one_hot = to_categorical(y_val, num_classes=len(classes))
        new_model.compile(optimizer='adam', loss=focal_loss, metrics=['accuracy'])

        # early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
        target_accuracy = 0.95
        early_stopping = CustomEarlyStoppingByAccuracy(monitor='accuracy', target=target_accuracy, verbose=1)
        new_model.fit(X_train, y_train_one_hot, validation_data=(X_val, y_val_one_hot), epochs=200, callbacks=[early_stopping], verbose=1)

    return new_model, tokenizer
    