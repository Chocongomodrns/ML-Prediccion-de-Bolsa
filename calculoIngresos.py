import numpy as np

saldo = 30700
comision = 1
dias = 60
saldoActual = saldo
i = 1
print(f"Saldo: {saldo}")

while i <= dias:
   i += 1
   saldoActual *= 1.03
   saldoActual -= comision
   if i % 15 == 0:
      print(f"Dia {i}: {saldoActual}")