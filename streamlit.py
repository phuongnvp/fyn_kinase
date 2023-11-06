# -*- coding: utf-8 -*-
"""
Created on Tue Oct 31 15:02:29 2023

@author: WINDOWS
"""
import pandas as pd
import pickle
import streamlit as st
from streamlit_option_menu import option_menu
import joblib
import pubchempy as pcp
import numpy as np                
import pandas as pd               
import matplotlib.pyplot as plt   
import seaborn as sns
from rdkit.Chem import Draw, Descriptors, rdqueries
from rdkit import RDLogger  
RDLogger.DisableLog('rdApp.*')  
from rdkit import Chem
import random
import requests
import io

df = pd.read_csv('Fyn_kinase.csv')
y = df['Activity'].values
X_model = df.iloc[:, 0:100]
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X_model, y, test_size=0.3, random_state = 42)
from sklearn.neighbors import NearestNeighbors
k = 5
knn_model = NearestNeighbors(n_neighbors=k)
knn_model.fit(X_train)
threshold = 22.75

Predict_Result1 = ''
results1 = []

st.title('FYN KINASE SCREENING')

# Create a radio button to choose the mode
selected_mode = st.selectbox("Select Mode of Screening", ["Single Mode", "Batch Mode"])

# Depending on the user's choice, display different content
if selected_mode == "Single Mode":
    if st.button('Example'):
        smiles_input = 'COc1ccc(CNC(=O)c2cc3c4ccccc4n4c(=O)c5ccccc5c(n2)c34)cc1'
    else:
        smiles_input = st.text_input("Enter your structure!")

    if st.button('Result'):
        df1 = pd.DataFrame({'Smiles': smiles_input},index=[0])
        df1['mol'] = df1['Smiles'].apply(lambda x: Chem.MolFromSmiles(x)) 
        df1['mol'] = df1['mol'].apply(lambda x: Chem.AddHs(x))
        # Calculate mol2vec descriptors
        from mol2vec.features import mol2alt_sentence, mol2sentence, MolSentence, DfVec, sentences2vec
        from gensim.models import word2vec
        w2vec_model = word2vec.Word2Vec.load('model_300dim.pkl')
        df1['sentence'] = df1.apply(lambda x: MolSentence(mol2alt_sentence(x['mol'], 1)), axis=1)
        df1['mol2vec'] = [DfVec(x) for x in sentences2vec(df1['sentence'], w2vec_model, unseen='UNK')]
        # Create dataframe 
        X1 = np.array([x.vec for x in df1['mol2vec']])  
        X = pd.concat((pd.DataFrame(X1), df1.drop(['mol2vec', 'mol', 'sentence', 'Smiles'], axis=1)), axis=1)
        #Application of Domain
        distances, indices = knn_model.kneighbors(X)
        Di = np.mean(distances)
        if Di > threshold:
            result = 'Your compound is out of our application domain'
        else:
            # Load pretrained model
            model = joblib.load('model_fyn.pkl')
            y_prediction = model.predict(X.values)
            probs1 = np.round(model.predict_proba(X.values)[:, 1] * 100, 2)
            probs0 = np.round(model.predict_proba(X.values)[:, 0] * 100, 2)
            if y_prediction[0] == 1:
                result = f'Your compound is active with probality of {probs1[0]}%'
            else:
                result = f'Your compound is inactive with probality of {probs0[0]}%'
        st.success(result)