# Medidor de Consumo e Capacidade de Baterias com Raspberry Pi Pico W  

**Por que confiar no rótulo da bateria se você pode medir a verdade?**  
Este projeto nasceu da curiosidade (e um pouco de desconfiança) sobre a real capacidade das baterias que usamos no dia a dia. Se você já se perguntou se aqueles “3800mAh” são mesmo reais, este medidor é para você!  

---

## 📌 O que é?  
Um sistema baseado em **Raspberry Pi Pico W** capaz de medir, registrar e calcular com precisão a corrente consumida por um dispositivo, monitorando a tensão da bateria e desligando automaticamente a carga quando o limite mínimo é atingido.  

Assim, você descobre a capacidade real (em mAh) da sua bateria — sem achismos!  

---

## ⚙️ Como funciona?  
- Mede a **tensão da bateria** usando um divisor resistivo.  
- Mede a **corrente consumida** com um sensor **ACS712** e divisor de sinal.  
- Registra os dados em um **arquivo CSV** para análise posterior.  
- **Desliga automaticamente** a carga via relé quando a bateria atinge o limite de segurança.  
- Comunica-se via **UART** com o dispositivo testado para garantir um desligamento seguro.  
- Permite **calibração fácil** usando um multímetro para máxima precisão.  

---

## 🎯 Por que usar?  
- Validar a **capacidade real** de baterias novas ou usadas.  
- Testar o **consumo de projetos embarcados**.  
- Aprender sobre **eletrônica, automação e instrumentação** de forma prática e divertida.  

---

## 🔧 Componentes principais  
- Raspberry Pi Pico W  
- Sensor de corrente ACS712  
- Módulo relé 3V3  
- Diodo Schottky (proteção)  
- Capacitor de filtragem  
- Step-up DC-DC  
- Resistores para divisores de tensão  
- Bateria Li-ion 3,7V  

---

## 🔌 Conexões principais  

- **Bateria Li-ion 3,7V → Step-up DC-DC** (ajustado para 5,3V).  
- **Saída do Step-up → Diodo Schottky 1N5819 → Vsys do Pico W.**  
- **Capacitor de 10uF/50V** entre Vsys e GND (próximo ao Pico W).  
- **Divisor resistivo de tensão para Vbat (10k/2k7):**  
  - 10k entre Vsys e ADC26 (Pico W)  
  - 2k7 entre ADC26 e GND  
- **Sensor ACS712:**  
  - IP+ recebe a saída do Step-up  
  - IP- vai para o terminal COM do relé  
  - OUT do ACS712 passa por divisor (1k68 entre OUT e ADC27, 10k entre ADC27 e GND)  
- **Módulo relé:**  
  - Controle no GPIO15 do Pico W  
  - COM recebe IP- do ACS712  
  - NO vai para alimentação do Pico Simulador  
- **UART1:**  
  - TX (GP4) e RX (GP5) do Pico W conectados ao header UART do simulador  
- **Todos os GNDs interligados.**  

🔎 Veja o **diagrama visual** incluso neste repositório para referência detalhada.  

---

## 📊 Resultados  
Ao final do teste, você terá um **arquivo CSV** com todos os dados de tensão, corrente e capacidade acumulada (em mAh), pronto para análise no **Excel, Google Sheets ou Python**.  

💡 **Divirta-se descobrindo a verdade sobre suas baterias!**  

Se encontrar algo estranho, lembre-se:  
👉 *A bateria pode mentir, mas seu medidor não!*  

---

## Conclusão
Neste teste, foi possível medir a capacidade efetivamente entregue pela bateria ao circuito, levando em conta o uso de um conversor step-up para alimentar a carga em 5,35 V. Considerando as perdas do conversor, a capacidade real disponível para o sistema ficou em torno de 1000 mAh para este exemplar, valor significativamente diferente do informado no rótulo. É importante destacar que este resultado se refere apenas à unidade testada, nas condições e configurações utilizadas, podendo variar para outras baterias ou marcas. Recomenda-se sempre realizar medições práticas para validar a real performance de cada bateria em seu próprio contexto de uso.

---

## 📄 Licença  
Este projeto está licenciado sob a **MIT License**.  
