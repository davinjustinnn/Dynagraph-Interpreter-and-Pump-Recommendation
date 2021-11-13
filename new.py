import matplotlib.pyplot as plt
import numpy as np
import os
import tensorflow as tf
import pathlib
import pandas as pd
import cv2
import streamlit as st

import plotly.graph_objects as go


st.title('Pump Problem Detection')

df = pd.read_excel ('Input.xlsx', engine= 'openpyxl')

st.subheader('**Program Input**')

input = st.selectbox('Choose Input File: ',['Your File','Sample File'])

if input =='Your File':
    uploaded_file = st.file_uploader("Choose input file: ",type=['xlsx','xls'])

    if uploaded_file is None:
        df = pd.read_excel ('Input.xlsx', engine= 'openpyxl')
        
    else:
        df = pd.read_excel (uploaded_file, engine= 'openpyxl')
        

else: 
    file_opt = st.selectbox('Choose sample file input: ',['Input.xlsx'])
    
    df = pd.read_excel (file_opt, engine= 'openpyxl')




structure_opt = df['Structure'].unique().tolist()
structure_opt = [x for x in structure_opt if pd.isnull(x) == False]
Structure = st.selectbox("Choose your structure name: ",structure_opt)
#Structure = st.sidebar.text_input ("Type your structure name:")

well_opt = df[df['Structure'] == Structure]['Well Name']
well_opt = [x for x in well_opt if pd.isnull(x) == False]
Well = st.selectbox("Choose your well name:",well_opt)

location = df[(df['Structure']==Structure) & (df['Well Name']==Well)].index.values
location = location[0]

#Define Variable
#PSE Variable
RGL = df.at[int(location), 'Gas-Liquid Ratio\n(GLR)']
FVF = df.at[int(location), 'Formation Volume Factor\n(FVF)']
WF =  df.at[int(location), 'Water Cut\n(WF)']
Dp = df.at[int(location), 'Pump Diameter\n(Dp)']
SGl = df.at[int(location), 'Liquid SG\n(SGl)']
L = df.at[int(location), 'Sucker Rod Length\n(L)']
S = df.at[int(location), 'Stroke Length\n(S)']
ai = df.at[int(location), 'Ratio Sucker Rod and total length\n(ai)']
fri = df.at[int(location), 'Sucker Rod Area\n(fri)']
ft = df.at[int(location), 'Tubing Area\n(ft)']

#SP Variable
K1 = df.at[int(location), 'Weighting Coeff 1\n(K1)']
K2 = df.at[int(location), 'Weighting Coeff 2\n(K2)']
K3 =  df.at[int(location), 'Weighting Coeff 3\n(K3)']
K4 = df.at[int(location), 'Weighting Coeff 4\n(K4)']
LL = df.at[int(location), 'Liquid level\n(L)']
Q = df.at[int(location), 'Production Rate\n(Q)']
Lo = df.at[int(location), 'Gas Column @bottom dead center\n(Lo)']
Log = df.at[int(location), 'Gas Column @Top dead center\n(Log)']
PD = df.at[int(location), 'Plunger Displacement\n(PD)']
Er = df.at[int(location), 'Elasticity Modulus\n(Er)']
Ar = df.at[int(location), 'Rod Area\n(Ar)']
rhor = df.at[int(location), 'Rod Density\n(rhor)']
Lr = df.at[int(location), 'Rod Length\n(Lr)']
Fr = df.at[int(location), 'Rod Load\n(Fr)']
Med = df.at[int(location), 'Motor Driving Torque\n(Med)']
Mcsd = df.at[int(location), 'Crank Torque Std. Deviation\n(Mcsd)']
Angle = df.at[int(location), 'Motor Angle\n(Angle)']
Po = df.at[int(location), 'Motor Power without Load\n(Po)']
nh = df.at[int(location), 'Motor Rated Efficiency\n(nh)']
Ph = df.at[int(location), 'Motor Power with Load\n(Ph)']

#PUS Variable
load = df.at[int(location), 'Pumping Load\n(load)']
min_load = df.at[int(location), 'Min. Pumping Load\n(min_load)']
max_load =  df.at[int(location), 'Max. Pumping Load\n(max_load)']
PI = df.at[int(location), 'Productivity Index\n(PI)']
Pres = df.at[int(location), 'Reservoir Pressure\n(Pres)']
Pwf = df.at[int(location), 'Well Flowing Pressure\n(pwf)']

#Pumping System Efficiency
def PSE (RGL, FVF, WF, Dp, SGl, L, S, ai, ft, fri):
    temp = 100*((1.1/(1+RGL))-0.1)*(1/(FVF*(1-WF)+WF))*0.8924*(1-((Dp*Dp)*SGl*L/(2.62*(10**11)*S))*((ai/fri)+(1/ft)))
    return temp

PSEResult = PSE (RGL, FVF, WF, Dp, SGl, L, S, ai, ft, fri)
if (PSE (RGL, FVF, WF, Dp, SGl, L, S, ai, ft, fri)<40):
    ans = "Pumping System Not Efficient"
else:
    ans = "Pumping System Efficient Enough"

#Swabbing Parameter
def SP (K1, K2, K3, K4, LL, Q, Lo, Log, PD, Er, Ar, rhor, Lr, Fr, Mcsd, Med, Angle, Po, nh, Ph):
    epf= L-Q-(Lo-Log)/PD
    FRL= Er*Ar*((2/(rhor*Ar*Lr))**0.5)*((3.14/2*L)+Fr)
    Pm= (Med*Angle)+Po+(((1/nh)-1)*Ph-Po)*((Med*Angle/Ph)**2)
    res= (K1*epf)+(K2*FRL)+(K3*Mcsd)+(K4*Pm)
    return res

SPResult = SP (K1, K2, K3, K4, LL, Q, Lo, Log, PD, Er, Ar, rhor, Lr, Fr, Mcsd, Med, Angle, Po, nh, Ph)

if (SP (K1, K2, K3, K4, LL, Q, Lo, Log, PD, Er, Ar, rhor, Lr, Fr, Mcsd, Med, Angle, Po, nh, Ph)>=0):
    ans2 = "Pumping design is already optimum"
else :
    ans2 = "Pumping design is not optimum"

#Real Time Data
#Pumping Unit System
def PUS (load, min_load, max_load, PI, Pres, Pwf):
    #Basic Calculation
    AOF= PI*Pres
    Qo= PI*(Pres-Pwf)
    Opt_low= 0.9*0.8*AOF
    Opt_high= 1.1*0.8*AOF
    
    #Conditional
    if (load<min_load):
        hasil = "Swabbing with other wells, pumping load is under the minimum load"
    elif (load>max_load):
        hasil = "Swabbing with other wells, pumping load is more than the maximum load"
    elif (load>min_load & load<max_load & Qo>Opt_low & Qo<Opt_high):
        hasil = "Change running parameter or update SRP downhole equipment size"
    elif (load>max_load & Qo>Opt_low & Qo<Opt_high):
        hasil = "Upgrade pump unit"
    elif (Qo<Opt_low):
        hasil = "Check well productivity, production rate is under the optimum point"
    elif (Qo>Opt_high):
        hasil = "Check well productivity, production rate is more than the optimum point"
    return hasil

PUSResult = PUS (load, min_load, max_load, PI, Pres, Pwf)

#st.write("Structure",Structure)
#st.write("Well", Well)
a = '''st.write("Pumping System Efficiency Value (%)",round(PSEResult,4))
st.write("Remarks :", ans)
st.write("Swabbing Parameter Analysis Value",round(SPResult,2))
st.write("Remarks: ",ans2)
st.write("Pumping Unit System Analysis Remarks :",PUSResult)
'''
data = [[Structure,Well,round(PSEResult,4),round(SPResult,2),PUSResult]]

output_df = pd.DataFrame(data,columns=["Structure","Well","Pumping System Efficiency Value (%)","Swabbing Parameter Analysis Value","Pumping Unit System Analysis Remarks"])

output_df=output_df.set_index('Structure')



st.subheader('**Input Data **')
st.write(df)



st.subheader('**Program Output**')
st.table(output_df)

