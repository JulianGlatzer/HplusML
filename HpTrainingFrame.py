"""Module with class that provides the H+ data for machine learning functions"""
import numpy as np
import HpMLUtils

class HpTrainingFrame:
    """Class that provides the H+ data for machine learning functions"""
    
    def __init__(self, pandasframe, backgroundclass=0):
        """Constructor which sets the pandas data frame and the class label for background"""

        self.pandasframe=pandasframe
        self.backgroundclass=backgroundclass
        self.feature_names=["nJets","nBTags_70","pT_jet1","Mbb_MindR_70","pT_jet5","H1_all","dRbb_avg_70","dRlepbb_MindR_70","Muu_MindR_70","HT_jets","Mbb_MaxPt_70","Mbb_MaxM_70","Mjjj_MaxPt","Centrality_all"]
        
    def get_pandasframe_mask(self, region, hpmass):
        """return as mask (true/false) of which events are to be included in the different samples (e.g. removes unwanted H+ masses)
        region: string name of the region
        hpmass: string "multi" or integer specifying the H+ mass
        """
        
        if hpmass=="multi":
            return self.pandasframe.region==region
        regionseries=self.pandasframe.region==region
        issignalseries=self.pandasframe.process=="Hp"+str(hpmass)
        isbackgroundseries=~self.pandasframe.process.str.contains("Hp")
        return regionseries & (issignalseries | isbackgroundseries)

    def get_features_classes_weights(self,region, hpmass,addMass=False):
        """returns a features data frame, a classes and a weights Series
           region: string, region of the events to be returned
           hpmass: string "multi" or integer specifying the H+ mass
           addMass: bool if True the truth H+ mass is added to the feature matrix (for parameterized ML training)
        """
        
        mask=self.get_pandasframe_mask(region, hpmass)
        if addMass:
            features=self.pandasframe[mask].loc[:,self.feature_names+["hpmass"]].copy()
        else:
            features=self.pandasframe[mask].loc[:,self.feature_names].copy()
        weights=abs(self.pandasframe[mask].weight)
        if hpmass=="multi":
            classes=self.pandasframe[mask].process.apply(lambda mass: self.backgroundclass if not "Hp" in mass else float(mass.replace("Hp","")))
        else:
            classes=self.pandasframe[mask].process.apply(lambda mass: self.backgroundclass if not "Hp" in mass else 1)
        features.reset_index(inplace = True, drop=True)
        weights.reset_index(inplace = True, drop=True) 
        classes.reset_index(inplace = True, drop=True)
        return features, classes, weights

    def get_split_series(self, region, hpmass, digits_train=np.linspace(0,98,50), digits_test=np.linspace(1,99,50)):
        """return a series of integers 0,1,2 which sample of training, testing and evaluation an event belongs to. The events are categorized according to whether the last two digits of the event number are in the np array digits_train, digits_test or none of the two.

           region: string, region of the events to be returned
           hpmass: string "multi" or integer specifying the H+ mass
           digits_train: see above
           digits_test: see above
        """
        
        mask=self.get_pandasframe_mask(region, hpmass)
        return self.pandasframe[mask].eventNumber.apply(lambda x: 0 if x%100 in digits_train else 1 if x%100 in digits_test else 2)

    def prepare(self, region="INC_ge6jge4b", hpmass="multi", shuffle=True, addMass=False):
        """ returns feature matrices, class labels and weights for training, testing and evaluation datasets (X_train, y_train, w_train, X_test, y_test, w_test, X_eval, y_eval, w_eval)
            region: string, region of the events to be returned
            hpmass: string "multi" or integer specifying the H+ mass
            shuffle: bool, if true events will be shuffled
            addMass: bool if True the truth H+ mass is added to the feature matrix (for parameterized ML training)
        """

        features, classes, weights=self.get_features_classes_weights(region,hpmass, addMass=addMass)
        split_series=self.get_split_series(region, hpmass)
        return HpMLUtils.train_test_split3(features,classes,weights, shuffle=shuffle, test_fold=split_series)