import string
from itertools import product
import pyzipper
import time
import multiprocessing
import threading
import os
from tkinter import Tk, filedialog, messagebox, simpledialog, Toplevel, Label, Button

# --- MOTOR DE BUSCA ---
def verificar_senha_worker(args):
    arquivo, senha = args
    try:
        with pyzipper.AESZipFile(arquivo) as zf:
            zf.read(zf.namelist()[0], pwd=bytes(senha, 'utf-8'))
            return senha
    except Exception:
        return None

class ZipTurboFinal:
    def __init__(self):
        self.root = Tk()
        self.root.withdraw()
        self.executando = False
        self.tentativas = 0
        self.inicio_tempo = 0
        self.caracteres = ""
        self.n_cores = 2

    def iniciar(self):
        # Seleção de Arquivo com Verificação
        arquivo = filedialog.askopenfilename(title="Selecionar ZIP", filetypes=[("Zip Files", "*.zip")])
        if not arquivo: 
            self.fechar_total()

        # Seleção de Núcleos com Verificação de Cancelamento
        max_cores = multiprocessing.cpu_count()
        escolha_cores = simpledialog.askinteger("Hardware", 
                                                f"Seu PC tem {max_cores} núcleos.\nQuantos deseja utilizar?", 
                                                initialvalue=2, minvalue=1, maxvalue=max_cores)
        
        if escolha_cores is None: 
            self.fechar_total()
        self.n_cores = escolha_cores

        # Configuração de Máscara com Verificação
        mascara = simpledialog.askstring("Setup", "Máscara (ex: A**) ou Vazio (1-6):")
        if mascara is None: 
            self.fechar_total()

        # Seletor de Caracteres
        opcoes = [(string.digits, "Números?"), (string.ascii_lowercase, "Letras Minúsculas?"), 
                (string.ascii_uppercase, "Letras Maiúsculas?"), (string.punctuation, "Símbolos?")]
        
        for chars, msg in opcoes:
            # Se fechar a janela de pergunta no X, o script assume 'Não' por segurança
            resposta = messagebox.askyesno("Dicionário", msg)
            if resposta:
                self.caracteres += chars
        
        if not self.caracteres: 
            self.caracteres = string.digits

        # Janela de Dashboard
        self.janela = Toplevel()
        self.janela.title("Recuperador Profissional")
        self.janela.geometry("400x320")
        self.janela.resizable(False, False)
        self.janela.configure(bg="#1A1A1B")
        self.janela.protocol("WM_DELETE_WINDOW", self.fechar_total)
        
        Label(self.janela, text="MONITORAMENTO DE PERFORMANCE", bg="#1A1A1B", fg="#F1C40F", font=("Arial", 10, "bold")).pack(pady=15)
        Label(self.janela, text=f"NÚCLEOS ATIVOS: {self.n_cores}", bg="#1A1A1B", fg="#3498DB", font=("Arial", 9, "bold")).pack()

        self.lbl_tentativas = Label(self.janela, text="Tentativas: 0", bg="#1A1A1B", fg="white", font=("Consolas", 11))
        self.lbl_tentativas.pack(pady=5)
        
        self.lbl_vazao = Label(self.janela, text="Velocidade: 0 p/s", bg="#1A1A1B", fg="#888888", font=("Arial", 9))
        self.lbl_vazao.pack()

        self.lbl_tempo = Label(self.janela, text="Tempo: 0.0s", bg="#1A1A1B", fg="#00FF41", font=("Consolas", 12, "bold"))
        self.lbl_tempo.pack(pady=10)

        Button(self.janela, text="CANCELAR TUDO", command=self.fechar_total, bg="#E74C3C", fg="white", width=20, relief="flat").pack(pady=20)

        self.executando = True
        self.inicio_tempo = time.time()
        
        threading.Thread(target=self.atualizar_interface, daemon=True).start()
        threading.Thread(target=self.gerenciar_nucleos, args=(arquivo, mascara), daemon=True).start()
        self.root.mainloop()

    def fechar_total(self):
        """Mata todos os processos e encerra o Python instantaneamente."""
        self.executando = False
        os._exit(0)

    def atualizar_interface(self):
        while self.executando:
            try:
                tempo = time.time() - self.inicio_tempo
                if tempo > 0:
                    vazao = self.tentativas / tempo
                    self.lbl_vazao.config(text=f"Velocidade: {int(vazao)} senhas/seg")
                
                self.lbl_tentativas.config(text=f"Tentativas: {self.tentativas:,}")
                self.lbl_tempo.config(text=f"Tempo: {tempo:.1f}s")
                self.root.update()
                time.sleep(0.1)
            except Exception:
                break  

    def gerenciar_nucleos(self, arquivo, mascara):
        if mascara:
            idx = [i for i, c in enumerate(mascara) if c == '*']
            gen = (self.montar_senha(mascara, idx, c) for c in product(self.caracteres, repeat=len(idx)))
        else:
            gen = ("".join(c) for i in range(1, 7) for c in product(self.caracteres, repeat=i))

        with multiprocessing.Pool(processes=self.n_cores) as pool:
            for resultado in pool.imap_unordered(verificar_senha_worker, ((arquivo, s) for s in gen), chunksize=500):
                if not self.executando:
                    break
                self.tentativas += 1
                if resultado:
                    self.executando = False
                    messagebox.showinfo("SUCESSO", f"SENHA ENCONTRADA:\n\n{resultado}")
                    self.fechar_total()
                    return

    def montar_senha(self, m, idx, combo):
        s = list(m)
        for i, char in enumerate(combo):
            s[idx[i]] = char
        return "".join(s)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = ZipTurboFinal()
    app.iniciar()