# -*- coding: utf-8 -*-
#Se importan las librerías
from gurobipy import *
import xlrd
import pandas as pd
#Se importan las hojas del excel
book = xlrd.open_workbook('prm.xls')
sheet_1 = book.sheet_by_index(0)
sheet_2 = book.sheet_by_index(1)
sheet_3 = book.sheet_by_index(2)
sheet_4 = book.sheet_by_index(3)
sheet_5 = book.sheet_by_index(4)
sheet_6 = book.sheet_by_index(5)
sheet_7 = book.sheet_by_index(6)
sheet_8 = book.sheet_by_index(7)


def Lista1(sheet):
    Var=[]
    for k in range(1,sheet.nrows):
        Var.append(sheet.cell(k,0).value)
    return Var

#Funcion para llamar variables de 1 subindice requiere la hoja de la variable y la columna
def parametro1int(sheet,col): 
    Var={}
    key=0
    for k in range(1,sheet.nrows):    
        key=int(sheet.cell(k,0).value)
        Var[key]=sheet.cell(k,col).value
    return Var

def parametro1str(sheet,col): 
    Var={}
    key=0
    for k in range(1,sheet.nrows):    
        key=str(sheet.cell(k,0).value)
        Var[key]=sheet.cell(k,col).value
    return Var

#Función para llamar variables de 2 subindices. Requiere solo la hoja de la variable
#Lee una matriz cruzada
def parametro2(sheet): 
    Var={}
    for k in range (1,sheet.nrows):
        key=sheet.cell(k,0).value
        Var[key]={}
        for i in range(1,sheet.ncols):
            Var[key][i] = sheet.cell(k,i).value
    return Var

def parametroE(sheet): 
    Var={}
    for i in range(1,sheet.nrows):
        Var[i]={}
        for k in range (1,sheet.ncols):
            key=sheet.cell(k,0).value                
            Var[i][key] = sheet.cell(i,k).value
    return Var

def parametroB(sheet):
    Var = {}
    Tipo = ['Correccion','Supervision','Examen']
    Anos = ['Cuarto','Mencion','Internado']
    
    for k in range(1,sheet.nrows):
        Var[k]={}
        for a in Anos:
            Var[k][a]={}
            for t in Tipo:
                if sheet.cell(k,0).value == k and sheet.cell(k,1).value == a and sheet.cell(k,2).value == t:
                    Var[k][a][t] = 1
                else:
                    Var[k][a][t] = 0
    return Var


#Funcion para llamar la variable U (realizaccion de la actividad k en la semana s)
#Transforma la semana s en un vector del tamaño del horizonte de semanas donde la semana de realización vale 1
def parametroU(sheet):
    Var={}
    semanas=[]
    for i in range (1,sheet.nrows):
        semanas.append(int(sheet.cell(i,2).value))
    s_max=int(max(semanas))
    
    for k in range(1,sheet.nrows):
        Var[k]={}
        sem=semanas[k-1]
        centro = sheet.cell(k,1).value
        for j in range(1,sheet.nrows):
            key =  sheet.cell(j,0).value
            Var[k][key]={}
            for s in range(1,s_max+1):
                if centro == key and sem == s :
                    Var[k][key][s] = 1
                else:
                    Var[k][key][s] = 0
    return Var


##Generación de parámetros en sus respectivas variables
T = parametro1int(sheet_1,1) #tiempo de realización de la actividad "k" en horas

D = parametro1str(sheet_2,1) #Disponibilidad horaria semanal del profesor "p"
N = parametro1str(sheet_2,2) #Holgura de cantidad de horas de sobrecarga profesor "P"
H = parametro1str(sheet_2,3) #Costo por hora de sobrecarga del profesor "p"

#   Y = parametro1str(sheet_5,1) #Puede mas de in profesor visitar el centro "j"? 1=si 0=no
M = parametro1str(sheet_5,2) # Numero de supervisiones totales que se realizan en el centro "j"

U = parametroU(sheet_3) # 1 si la actividad "k" se realiza en la semana "s"
#C = parametro2(sheet_4) # Costo de que el profesor "p" realice la actividad "k"
E = parametroE(sheet_7) # Si el profesor posee la misma specialidad de la actividad "k"

B = parametroB(sheet_6) # Tipo y año de la actividad "k"



##Prioridades y pesos de la función objetivo. Valores ejemplo
SetObjPriority = [3, 2]
SetObjWeight   = [1.0, 0.25]


##Crear Modelo
m = Model("modelo1")


##Largos
#Especialidades = Lista1(sheet_8)
P=len(D) #P: cantidad total de profesores 
K=len(U) #K: cantidad de actividades

semanas=[]
for i in range (1,sheet_3.nrows):
    semanas.append(int(sheet_3.cell(i,2).value))
S=max(semanas)

R=len(B[1])
L=len(B[1]['Cuarto'])
J =len(M)


    
## Variable de decision
x = {}
# Para cada profesor
for p in N:
    # agregar una lista
    x[p]={}
    # para cada especialidad crear lista y añadir variable binaria. 1 si el profesor realiza la actividad k
    for k in range(1,K+1):
        x[p][k]=m.addVar(vtype=GRB.BINARY, name="x[%s,%d]"%(p,k))
        
        
        
Z = {}
# Para cada profesor
for p in N:
    # agregar una lista
    Z[p]={}
    # para cada especialidad crear lista y añadir variable binaria. 1 si el profesor realiza la actividad k
    for s in range(1,S+1):
        Z[p][s]=m.addVar(vtype=GRB.BINARY, name="Z[%s,%d]"%(p,s))
        
        
        
G = {}
# Para cada profesor
for p in N:
    # agregar una lista
    G[p]={}
    for j in M:
        G[p][j]=m.addVar(vtype=GRB.BINARY, name="G[%s,%s]"%(p,j))
        
        



#Setea el objetivo del modelo
m.ModelSense = GRB.MINIMIZE



## Restricciones
#1. Capacidad profesor. Un profesor no puede realizar más actividades que su capacidad + holgura
for p in N:    
    for s in range(1,S+1):
        lexp = LinExpr()       
        for k in U.keys():
            for j in U[k].keys():                
                lexp.addTerms(U[k][j][s]*T[k], x[p][k])                
        m.addConstr(lexp, GRB.LESS_EQUAL, D[p], name='C1')

        
##2. La cantidad de sobrecarga asignada debe ser menor o igual a la maxima carga extra
for p in N:
    for s in range(1,S+1):
        lexp_2=LinExpr()
        lexp_2.addTerms(1, Z[p][s])
        m.addConstr(lexp_2, GRB.LESS_EQUAL, D[p], name='')

        
Aj={}
for j in M: #Para cada centro
    key_j = j
    Aj[key_j]=[]
    for k in range(1,sheet_3.nrows): #Para cada actividad
        if sheet_3.cell(k,1).value == key_j: #Si la actividad corresponde al centro
            Aj[key_j].append(k)                

##3.1

Pract_Tipe = ['Cuarto', 'Internado', 'Mencion']
Act_Tipe = ['Supervision', 'Correccion', 'Examen']

for j in Aj.keys(): #para todos los centros con sus respectivas actividades
    for p in N: #para todo profesor
        lexp_3_1 = LinExpr()
        for k in Aj[j]: #sumar todas las actividades en ese centro            
            for r in Pract_Tipe: #para cada tipo de practica                         
                lexp_3_1.addTerms(B[k][r]['Supervision'], x[p][k])
        m.addConstr(lexp_3_1, GRB.LESS_EQUAL, M[j]*G[p][j], name= 'C1')        
    
##3.2
for j in Aj:
    for p in N:
        lexp_3_2=LinExpr()
        for k in Aj[j]:
            for r in B[1]:
                lexp_3_2.addTerms(B[k][r]['Supervision'], x[p][k])
        m.addConstr(G[p][j], GRB.LESS_EQUAL, lexp_3_2, name= 'C2')

##4
for j in M:
    lexp_4=LinExpr()
    for p in N:
        lexp_4.addTerms(1.0, G[p][j]) 
    m.addConstr(lexp_4, GRB.LESS_EQUAL, 1, name= 'C3')
    

##5
for k in range(1,K+1):
    lexp_5=LinExpr()
    for p in N:
        lexp_5.addTerms(1.0, x[p][k])
    m.addConstr(lexp_5, GRB.EQUAL, 1, name= 'C4')

##6
'''for p in N:
    for k in range(1,K+1):
        for r in B[1]:
            m.addConstr(x[p][k], GRB.LESS_EQUAL, B[k][r]['Correccion']*E[p][k], name= 'C5')


##7
for p in N:
    for k in range(1,K+1):
        for r in B[1]:
            m.addConstr(x[p][k], GRB.LESS_EQUAL, B[k][r]['Examen']*E[p][k], name= 'C6')
'''

##Funcion Objetivo
Obj={}
Obj[0]=LinExpr()
Obj[1]=LinExpr()

for p in N:
    for k in range(1,K+1):
        Obj[0].addTerms(10, x[p][k])
    for s in range(1,S+1):
        Obj[1].addTerms(H[p], Z[p][s])

#OBJ = LinExpr()
#OBJ.add(Obj[0], 1)
#OBJ.add(Obj[1], 1)
for e in Obj.keys():
    m.setObjectiveN(Obj[e], e, SetObjPriority[e], SetObjWeight[e], name='Set' + str(e))

#m.setObjectiveN(OBJ, GRB.MINIMIZE)
m.write('modelo.lp')
m.optimize()

df = pd.DataFrame(x)
df

SUM_Valores = {}
for p in N.keys():
    SUM_Valores[p] = 0
    for i in range(1,K):
        SUM_Valores[p]+=x[p][i].X
print (SUM_Valores)

'''
for v in m.getVars():
        print('%s %g' % (v.varName, v.x))

print('Obj: %g' % m.objVal)'''


'''
for k in range(1,K+1):
    lexp_5=LinExpr()
    for p in N:
        lexp_5.addTerms(1.0, x[p][k])
    m.addConstr(lexp_5, GRB.EQUAL, 1, name= 'C4')
    '''