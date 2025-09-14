# measure_batt_acs_uart_auto_calibrated_handshake.py
from machine import Pin, ADC, UART
import time

# ---------- UART1 COM SIMULADOR ----------
uart1 = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))  # GP4=TX, GP5=RX

# ---------- PINOUT ----------
adc_vbat = ADC(Pin(26))   # GP26 -> VBAT divisor
adc_acs  = ADC(Pin(27))   # GP27 -> ACS OUT via divisor

# ---------- RELÉ ----------
RELAY_PIN = 15  # Exemplo: GP15 controla o relé 3V3
rele = Pin(RELAY_PIN, Pin.OUT)
rele.value(0)  # Inicialmente ligado (1 = alimentação liberada, depende do seu módulo)

# ---------- CONSTANTES ----------
ADC_MAX = 65535
VREF = 3.3

# Divisores resistivos
Rtop_vbat, Rbot_vbat = 10000.0, 2700.0
VBAT_FACTOR = Rbot_vbat / (Rtop_vbat + Rbot_vbat)

R1_acs, R2_acs = 1680.0, 10000.0
ACS_DIV_FACTOR = R2_acs / (R1_acs + R2_acs)

# Parâmetros do sensor ACS712 / compatível
ACS_SENSITIVITY_ORIGINAL = 0.185  # V/A para versão de 5A (ajuste se for 20A=0.100, 30A=0.066)
ACS_SENSITIVITY = ACS_SENSITIVITY_ORIGINAL

CURRENT_SCALE_FIX = 0.1   # Valor inicial
AUTO_SCALE_CALIB = True   # Ativar calibração com multímetro

SAMPLE_INTERVAL = 1.0     # segundos
MA_SAMPLES = 20           # média móvel
ADC_SETTLE_MS = 10

VBAT_CUTOFF = 3.0              # Volts
CUTOFF_COUNT_REQUIRED = 3      # leituras consecutivas

def adc_raw_read_with_settle(adc, settle_ms=ADC_SETTLE_MS):
    _ = adc.read_u16()
    if settle_ms:
        time.sleep_ms(settle_ms)
    return adc.read_u16()

def raw_to_vadc(raw):
    return (raw / ADC_MAX) * VREF

def read_vbat_raw():
    raw = adc_raw_read_with_settle(adc_vbat)
    vadc = raw_to_vadc(raw)
    vbat = vadc / VBAT_FACTOR
    return raw, vbat

def read_acs_raw():
    raw = adc_raw_read_with_settle(adc_acs)
    vadc = raw_to_vadc(raw)
    vacs = vadc / ACS_DIV_FACTOR
    return raw, vacs

def calibrate_acs(n=400, delay_ms=8):
    print("Calibrando ACS (garanta NENHUMA carga conectada)...")
    print(f"ACS sensibilidade nominal: {ACS_SENSITIVITY:.4f} V/A")
    print(f"Fator de correção inicial: {CURRENT_SCALE_FIX:.4f}")
    time.sleep(0.5)
    s = 0.0
    for _ in range(n):
        _, vacs = read_acs_raw()
        s += vacs
        time.sleep_ms(delay_ms)
    zero = s / n
    print("ACS zero (offset) = {:.4f} V".format(zero))
    return zero

def wait_for_ack(timeout=5):
    print("Aguardando ACK do simulador...")
    start = time.time()
    while (time.time() - start) < timeout:
        if uart1.any():
            resp = uart1.readline()
            if resp and b"ACK" in resp:
                print("ACK recebido do simulador.")
                return True
        time.sleep(0.1)
    print("Timeout aguardando ACK!")
    return False

def main():
    acs_zero = calibrate_acs()
    time.sleep(0.5)

    input("Calibração concluída (ACS zero = {:.4f} V). Pressione Enter após conectar a carga...".format(acs_zero))

    acs_buf = []
    cap_mAh = 0.0
    last_t = time.ticks_ms()
    cutoff_counter = 0
    start_time = time.time()
    scale_fix = CURRENT_SCALE_FIX
    did_scale_calibrate = False

    filename = "medicoes_auto_calibrated.csv"
    with open(filename, "w") as f:
        f.write("tempo_s,vbat_V,current_raw_A,current_real_A,cap_mAh_real,scale_factor\n")

    try:
        while True:
            t_now = time.ticks_ms()
            dt_s = time.ticks_diff(t_now, last_t) / 1000.0
            last_t = t_now

            _, vbat = read_vbat_raw()
            raw_a, vacs = read_acs_raw()

            acs_buf.append(vacs)
            if len(acs_buf) > MA_SAMPLES:
                acs_buf.pop(0)
            vacs_mean = sum(acs_buf) / len(acs_buf)

            current_raw = (vacs_mean - acs_zero) / ACS_SENSITIVITY

            if AUTO_SCALE_CALIB and not did_scale_calibrate and abs(current_raw) > 0.01:
                print("\n" + "="*60)
                print("🔧 CALIBRAÇÃO AUTOMÁTICA DE ESCALA")
                print("="*60)
                print(f"Corrente bruta calculada: {current_raw:.3f} A")
                print("Agora meça a corrente REAL com multímetro em série no fio de 5V")
                print("(entre saída do step-up e entrada IP+ do ACS, ou entre IP- e carga)")
                try:
                    mult_str = input("Digite a corrente lida no multímetro em A (ex: 0.40): ")
                    mult_current = float(mult_str.strip())
                    if abs(mult_current) > 1e-6 and abs(current_raw) > 1e-6:
                        scale_fix = mult_current / current_raw
                        print(f"✅ Novo fator de escala calculado: {scale_fix:.6f}")
                        print(f"   (multímetro: {mult_current:.3f} A / código bruto: {current_raw:.3f} A)")
                        did_scale_calibrate = True
                    else:
                        print("❌ Valores muito baixos, mantendo fator original")
                        scale_fix = CURRENT_SCALE_FIX
                except Exception as e:
                    print(f"❌ Erro na calibração: {e}")
                    print("Mantendo fator de correção original")
                    scale_fix = CURRENT_SCALE_FIX
                print("="*60)
                print("Continuando medição com fator calibrado...")
                print("="*60 + "\n")

            current_A = current_raw * scale_fix
            if -0.005 < current_A < 0.005:
                current_A = 0.0

            dt_h = dt_s / 3600.0
            cap_mAh += current_A * 1000.0 * dt_h

            elapsed = time.time() - start_time
            print("t={:.1f}s | Vbat={:.3f} V | I={:.3f} A | Cap={:.2f} mAh | Scale={:.6f}"
                  .format(elapsed, vbat, current_A, cap_mAh, scale_fix))

            with open(filename, "a") as f:
                f.write("{:.1f},{:.3f},{:.6f},{:.3f},{:.2f},{:.6f}\n"
                        .format(elapsed, vbat, current_raw, current_A, cap_mAh, scale_fix))

            if vbat <= VBAT_CUTOFF:
                cutoff_counter += 1
            else:
                cutoff_counter = 0

            if cutoff_counter >= CUTOFF_COUNT_REQUIRED:
                print("⚠️ Vbat={:.2f} V detectado. Enviando LOW_BATT via UART1.".format(vbat))
                uart1.write("LOW_BATT\n")
                if wait_for_ack(timeout=5):
                    print("Acionando relé para cortar alimentação do simulador.")
                    rele.value(1)  # Desliga o relé (ajuste conforme seu módulo: 0 ou 1)
                else:
                    print("ACK não recebido, relé NÃO acionado!")
                break

            time.sleep(SAMPLE_INTERVAL)

    except KeyboardInterrupt:
        print("\nMedição interrompida manualmente. Capacidade final = {:.2f} mAh".format(cap_mAh))

    print("Dados salvos em", filename)
    print(f"Fator de escala final usado: {scale_fix:.6f}")

if __name__ == "__main__":
    main()
