"""Module with several helper functions to build, train and evaluate H+ Keras models"""

from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras import regularizers
from sklearn.metrics import roc_auc_score
from keras.callbacks import Callback

class RocCallback(Callback):
    """ A Keras callback that calculates the ROC AUC"""

    def __init__(self,training_data,validation_data, verbose=True):
        self.verbose=verbose
        self.x = training_data[0]
        self.y = training_data[1]
        self.w = training_data[2]
        self.x_val = validation_data[0]
        self.y_val = validation_data[1]
        self.w_val = validation_data[2]
        self.roc=[]
        self.roc_val=[]

    def on_train_begin(self, logs={}):
        return

    def on_train_end(self, logs={}):
        return

    def on_epoch_begin(self, epoch, logs={}):
        return

    def on_epoch_end(self, epoch, logs={}):
        y_pred = self.model.predict(self.x)
        roc = roc_auc_score(self.y, y_pred, sample_weight=self.w)
        y_pred_val = self.model.predict(self.x_val)
        roc_val = roc_auc_score(self.y_val, y_pred_val, sample_weight=self.w_val)
        if self.verbose:
            print('\rroc-auc: %s - roc-auc_val: %s' % (str(round(roc,4)),str(round(roc_val,4))))
        self.roc_val.append(roc_val)
        self.roc.append(roc)
        return

    def on_batch_begin(self, batch, logs={}):
        return

    def on_batch_end(self, batch, logs={}):
        return

class HpFeedForwardModel():
    """ A simple feed forward NN based on Keras"""

    def __init__(self, configuration, l2treshold=None, dropout=None, verbose=True):
        """ constructor
        configuration: list of the number of nodes per layer, each item is a layer
        l2treshold: if not None a L2 weight regularizer with threshold <l2treshold> is added to each leayer
        dropout: if not None a dropout fraction of <dropout> is added after each internal layer
        verbose: if true the model summary is printed
        """
        
        self.callbacks = None
        self.configuration=configuration
        self.dropout=dropout
        self.l2threshold=l2threshold
        self.model = Sequential()
        for i,layer in enumerate(layers):
            if i==0:
                if l2treshold==None:
                    model.add(Dense(layer, input_dim=15, activation='relu'))    
                else:
                    model.add(Dense(layer, input_dim=15, activation='relu', kernel_regularizer=regularizers.l2(l2treshold)))    
            else:
                if l2treshold==None:
                    model.add(Dense(layer, activation='relu'))
                else:
                    model.add(Dense(layer, activation='relu', kernel_regularizer=regularizers.l2(l2treshold)))
            if dropout!=None:
                model.add(Dropout(rate=dropout))
        #final layer is a sigmoid for classification
        model.add(Dense(1, activation='sigmoid'))
        #model.add(Dense(5, activation='relu'))

        # Compile model
        model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['binary_accuracy'])
        if verbose:
            model.summary()

        return model
    
    def train(self, trainData, testData, epochs=100, patience=15):
        """ train the Keras model with Early stopping, will return test and training ROC AUC
        trainData: tuple of (X_train, y_train, w_train)
        trainData: tuple of (X_test, y_test, w_test)
        epochs: maximum number of epochs for training
        patience: patience for Early stopping based on validation loss
        """

        X_train=trainData[0]
        y_train=trainData[1]
        w_train=trainData[2]
        X_test=testData[0]
        y_test=testData[1]
        w_test=testData[2]

        if self.callbacks==None:
            self.callbacks=[EarlyStopping(monitor='val_loss', 
                                          patience=patience),
                            ModelCheckpoint(filepath='model_nn_'+str(self.configuration)+"_dropout"+self.dropout+"_l2threshold"+self.l2threshold+".hdf5", 
                                            monitor='val_loss',
                                            save_best_only=True),
                            RocCallback(training_data=trainData,validation_data=testData)
                            ]
        self.history=self.model.fit(X_train,y_train, sample_weight=w_train,
                                    batch_size=50, epochs=epochs, callbacks=self.callbacks,
                                    validation_data=testData)

        model.load_weights("model_nn_"+str(self.configuration)+"_dropout"+self.dropout+"_l2threshold"+self.l2threshold+".hdf5")
        y_pred_test=model.predict(X_test).ravel()
        y_pred_train=model.predict(X_train).ravel()
        roc_test =roc_auc_score(y_test,  y_pred_test,  sample_weight=w_test)
        roc_train=roc_auc_score(y_train, y_pred_train, sample_weight=w_train)
        #print(self.configuration, roc_test, roc_train)
        
        return roc_test, roc_train

    def plotTrainingValidation(self):
        """draws plots for loss, binary accuracy and ROC AUC"""

        loss_values=self.history.history['loss']
        val_loss_values=self.history.history['val_loss']
        acc_values=self.history.history['binary_accuracy']
        val_acc_values=self.history.history['val_binary_accuracy']

        rocauc_values=None
        val_rocauc_values=None
        for cb in self.callbacks:
            if hasattr(cb, 'property'):
                rocauc_values=cb.roc
                val_rocauc_values=cb.roc_val


        bestepoch=callbacks[0].stopped_epoch-callbacks[0].patience+1
  
        epochs=range(1,len(acc_values)+1)
        plt.figure()
        plt.plot(epochs, loss_values, "bo",label="Training loss")
        plt.plot(epochs, val_loss_values, "b",label="Validation loss")
        plt.legend(loc=0)
        plt.xlabel("Epochs")
        plt.ylabel("Loss")
        plt.axvline(x=bestepoch)

        ax=plt.figure()
        plt.plot(epochs, acc_values, "bo",label="Training acc")
        plt.plot(epochs, val_acc_values, "b",label="Validation acc")
        plt.legend(loc=0)
        plt.xlabel("Epochs")
        plt.ylabel("Accuracy")
        plt.axvline(x=bestepoch)

        if not rocauc_values is None:
            ax=plt.figure()
            plt.plot(epochs, rocauc_values, "bo",label="Training ROC AUC")
            plt.plot(epochs, val_rocauc_values, "b",label="Validation ROC AUC")
            plt.legend(loc=0)
            plt.xlabel("Epochs")
            plt.ylabel("ROC AUC")
            plt.axvline(x=bestepoch)