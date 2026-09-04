#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculadora de Energia de Coesão para SIESTA
Versão CORRIGIDA - Lê quantidades do bloco de coordenadas
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import re
import os
from datetime import datetime

class CohesiveEnergyCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora de Energia de Coesão - SIESTA")
        self.root.geometry("1100x850")
        
        # Dados do sistema
        self.system_file = None
        self.system_energy = None
        self.system_atoms = 0
        self.system_species = []        # Lista de (idx, atomic_number, pseudo)
        self.species_counts = {}        # {idx: count} - AGORA CORRETO!
        
        # Dados dos átomos isolados
        self.atom_energies = {}
        self.atom_files = {}
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configura a interface"""
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(main_frame, text="Calculadora de Energia de Coesão - SIESTA", 
                 font=('Arial', 14, 'bold')).pack(pady=5)
        
        # Frame do sistema
        sys_frame = ttk.LabelFrame(main_frame, text="1. SISTEMA", padding=10)
        sys_frame.pack(fill=tk.X, pady=5)
        
        btn_frame = ttk.Frame(sys_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Carregar .out do sistema", 
                  command=self.load_system).pack(side=tk.LEFT, padx=5)
        
        self.sys_label = ttk.Label(btn_frame, text="Nenhum arquivo", foreground="gray")
        self.sys_label.pack(side=tk.LEFT, padx=10)
        
        self.sys_info = tk.Text(sys_frame, height=8, width=100, state='disabled', font=('Courier', 9))
        self.sys_info.pack(fill=tk.X, pady=5)
        
        # Frame dos átomos
        atom_frame = ttk.LabelFrame(main_frame, text="2. ÁTOMOS ISOLADOS", padding=10)
        atom_frame.pack(fill=tk.X, pady=5)
        
        self.atom_controls = ttk.Frame(atom_frame)
        self.atom_controls.pack(fill=tk.X, pady=5)
        
        self.atom_info = tk.Text(atom_frame, height=6, width=100, state='disabled', font=('Courier', 9))
        self.atom_info.pack(fill=tk.X, pady=5)
        
        # Frame de cálculo
        calc_frame = ttk.LabelFrame(main_frame, text="3. CÁLCULO", padding=10)
        calc_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(calc_frame, text="CALCULAR ENERGIA DE COESÃO", 
                  command=self.calculate).pack(pady=5)
        
        # Frame de resultados
        res_frame = ttk.LabelFrame(main_frame, text="4. RESULTADOS", padding=10)
        res_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.result_text = scrolledtext.ScrolledText(res_frame, height=12, width=100, 
                                                    state='disabled', font=('Courier', 10))
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # Botões
        btn_bottom = ttk.Frame(main_frame)
        btn_bottom.pack(pady=10)
        ttk.Button(btn_bottom, text="Salvar resultados", 
                  command=self.save_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_bottom, text="Limpar", 
                  command=self.clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_bottom, text="Sair", 
                  command=self.root.quit).pack(side=tk.LEFT, padx=5)
    
    def read_siesta_energy(self, filepath):
        """Lê a energia total do arquivo .out"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Procura de baixo para cima
            for line in reversed(lines):
                match = re.search(r'siesta:\s*Etot\s*=\s*([-\d.]+)', line, re.IGNORECASE)
                if match:
                    return float(match.group(1))
                
                match = re.search(r'Total\s+energy\s*=\s*([-\d.]+)', line, re.IGNORECASE)
                if match:
                    return float(match.group(1))
            
            return None
        except:
            return None
    
    def read_system_info(self, filepath):
        """
        Lê informações do sistema do .out
        RETORNA: n_atoms, species, species_counts, content
        """
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 1. Número total de átomos
            n_atoms = None
            match = re.search(r'NumberOfAtoms\s+(\d+)', content, re.IGNORECASE)
            if match:
                n_atoms = int(match.group(1))
            
            # 2. Espécies químicas do bloco ChemicalSpeciesLabel
            species = []
            block_pattern = r'%block\s+ChemicalSpeciesLabel\s+(.*?)(?:%endblock|$|\n\s*\n)'
            match = re.search(block_pattern, content, re.DOTALL | re.IGNORECASE)
            
            if match:
                block_content = match.group(1)
                for line in block_content.strip().split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split()
                        if len(parts) >= 3:
                            try:
                                idx = int(parts[0])
                                atomic_number = parts[1]
                                pseudo = parts[2]
                                species.append((idx, atomic_number, pseudo))
                            except ValueError:
                                continue
            
            # 3. CONTAGEM DE CADA ESPÉCIE - LENDO O BLOCO DE COORDENADAS!
            species_counts = {}
            
            # Procura pelo bloco de coordenadas atômicas
            coord_patterns = [
                r'%block\s+AtomicCoordinatesAndAtomicSpecies\s+(.*?)(?:%endblock|$|\n\s*\n)',
                r'%block\s+AtomicCoordinatesAndSpecies\s+(.*?)(?:%endblock|$|\n\s*\n)',
                r'%block\s+AtomicCoordinates\s+(.*?)(?:%endblock|$|\n\s*\n)'
            ]
            
            coord_block = None
            for pattern in coord_patterns:
                match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
                if match:
                    coord_block = match.group(1)
                    break
            
            if coord_block:
                # Conta quantas vezes cada espécie aparece
                for line in coord_block.strip().split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split()
                        if len(parts) >= 4:  # x y z species_index
                            try:
                                species_idx = int(parts[3])
                                species_counts[species_idx] = species_counts.get(species_idx, 0) + 1
                            except (ValueError, IndexError):
                                pass
                
                # Verifica se a contagem bate com NumberOfAtoms
                total_counted = sum(species_counts.values())
                if n_atoms is not None and total_counted != n_atoms:
                    print(f"Aviso: Contagem ({total_counted}) != NumberOfAtoms ({n_atoms})")
            
            # Se não encontrou coordenadas, tenta método alternativo
            if not species_counts and species:
                # Tenta extrair do SystemName como fallback
                sys_name_match = re.search(r'SystemName\s+(\S+)', content, re.IGNORECASE)
                if sys_name_match:
                    name = sys_name_match.group(1)
                    for idx, atomic_num, pseudo in species:
                        symbol = re.sub(r'\..*$', '', pseudo)
                        symbol = re.sub(r'[0-9]', '', symbol)
                        pattern = f'{symbol}(\\d+)'
                        match = re.search(pattern, name, re.IGNORECASE)
                        if match:
                            species_counts[idx] = int(match.group(1))
                        else:
                            species_counts[idx] = 1
                else:
                    # Último recurso: divide igualmente
                    if len(species) > 0 and n_atoms:
                        base = n_atoms // len(species)
                        remainder = n_atoms % len(species)
                        for i, (idx, _, _) in enumerate(species):
                            species_counts[idx] = base + (1 if i < remainder else 0)
                    else:
                        for idx, _, _ in species:
                            species_counts[idx] = 1
            
            return n_atoms, species, species_counts, content
            
        except Exception as e:
            print(f"Erro: {e}")
            return None, [], {}, ""
    
    def load_system(self):
        """Carrega o arquivo .out do sistema"""
        filepath = filedialog.askopenfilename(
            title="Selecione o .out do sistema",
            filetypes=[("Arquivos SIESTA", "*.out"), ("Todos", "*.*")]
        )
        
        if not filepath:
            return
        
        self.system_file = filepath
        self.sys_label.config(text=os.path.basename(filepath), foreground="green")
        
        # Ler energia
        energy = self.read_siesta_energy(filepath)
        if energy is not None:
            self.system_energy = energy
        else:
            self.system_energy = None
            messagebox.showwarning("Aviso", "Energia não encontrada no arquivo!")
        
        # Ler informações completas
        n_atoms, species, species_counts, content = self.read_system_info(filepath)
        self.system_atoms = n_atoms if n_atoms is not None else 0
        self.system_species = species
        self.species_counts = species_counts
        
        # Log das contagens
        self.log(f"Sistema carregado: {os.path.basename(filepath)}", "INFO")
        self.log(f"Total de átomos: {self.system_atoms}", "INFO")
        for idx, atomic_num, pseudo in species:
            symbol = re.sub(r'\..*$', '', pseudo)
            symbol = re.sub(r'[0-9]', '', symbol)
            count = species_counts.get(idx, 0)
            self.log(f"  Espécie [{idx}] {symbol}: {count} átomos", "INFO")
        
        if energy is not None:
            self.log(f"Energia total: {energy:.6f} eV", "INFO")
        
        # Atualizar interface
        self.update_system_display()
        self.create_atom_buttons()
    
    def create_atom_buttons(self):
        """Cria botões para cada espécie"""
        # Limpar controles antigos
        for widget in self.atom_controls.winfo_children():
            widget.destroy()
        
        if not self.system_species:
            return
        
        for idx, atomic_num, pseudo in self.system_species:
            # Extrai símbolo do pseudopotencial
            symbol = re.sub(r'\..*$', '', pseudo)
            symbol = re.sub(r'[0-9]', '', symbol)
            count = self.species_counts.get(idx, 1)
            
            frame = ttk.Frame(self.atom_controls)
            frame.pack(side=tk.LEFT, padx=10, pady=5)
            
            btn = ttk.Button(frame, 
                           text=f"{symbol} x{count}",
                           command=lambda i=idx: self.load_atom(i))
            btn.pack()
            
            label = ttk.Label(frame, text="Não carregado", foreground="gray")
            label.pack()
            
            # Armazena referências
            frame.btn = btn
            frame.label = label
            frame.idx = idx
            frame.symbol = symbol
            frame.count = count
    
    def load_atom(self, idx):
        """Carrega o .out de um átomo isolado"""
        # Encontra a espécie
        species_info = None
        for i, atomic_num, pseudo in self.system_species:
            if i == idx:
                symbol = re.sub(r'\..*$', '', pseudo)
                symbol = re.sub(r'[0-9]', '', symbol)
                species_info = (i, atomic_num, pseudo, symbol)
                break
        
        if not species_info:
            return
        
        idx, atomic_num, pseudo, symbol = species_info
        
        filepath = filedialog.askopenfilename(
            title=f"Selecione o .out do {symbol} isolado",
            filetypes=[("Arquivos SIESTA", "*.out"), ("Todos", "*.*")]
        )
        
        if not filepath:
            return
        
        # Ler energia
        energy = self.read_siesta_energy(filepath)
        if energy is not None:
            self.atom_energies[idx] = energy
            self.atom_files[idx] = filepath
            
            # Atualizar label
            for widget in self.atom_controls.winfo_children():
                if hasattr(widget, 'idx') and widget.idx == idx:
                    widget.label.config(text=f"{energy:.6f} eV", foreground="green")
            
            self.log(f"{symbol} isolado: {energy:.6f} eV", "INFO")
        else:
            messagebox.showwarning("Aviso", f"Energia não encontrada para {symbol}!")
        
        self.update_atom_display()
    
    def update_system_display(self):
        """Atualiza a exibição das informações do sistema"""
        text = f"Arquivo: {os.path.basename(self.system_file) if self.system_file else 'Nenhum'}\n"
        text += f"Número total de átomos: {self.system_atoms}\n"
        
        if self.system_species:
            text += "\nEspécies e quantidades (lidas do bloco de coordenadas):\n"
            for idx, atomic_num, pseudo in self.system_species:
                symbol = re.sub(r'\..*$', '', pseudo)
                symbol = re.sub(r'[0-9]', '', symbol)
                count = self.species_counts.get(idx, 0)
                text += f"  [{idx}] {symbol} (Z={atomic_num}) x{count}  →  {pseudo}\n"
        
        if self.system_energy is not None:
            text += f"\nEnergia total: {self.system_energy:.8f} eV"
        
        self.sys_info.config(state='normal')
        self.sys_info.delete(1.0, tk.END)
        self.sys_info.insert(1.0, text)
        self.sys_info.config(state='disabled')
    
    def update_atom_display(self):
        """Atualiza a exibição dos átomos carregados"""
        if not self.atom_files:
            text = "Nenhum átomo carregado."
        else:
            text = "Átomos carregados:\n"
            for idx in sorted(self.atom_files.keys()):
                energy = self.atom_energies.get(idx)
                filepath = self.atom_files.get(idx, "")
                count = self.species_counts.get(idx, 0)
                text += f"  [{idx}] {os.path.basename(filepath)} (x{count}): "
                text += f"{energy:.6f} eV\n" if energy is not None else "❌ Energia não encontrada\n"
        
        self.atom_info.config(state='normal')
        self.atom_info.delete(1.0, tk.END)
        self.atom_info.insert(1.0, text)
        self.atom_info.config(state='disabled')
    
    def calculate(self):
        """Calcula a energia de coesão"""
        if self.system_energy is None:
            messagebox.showerror("Erro", "Sistema sem energia!")
            return
        
        if not self.atom_energies:
            messagebox.showerror("Erro", "Carregue os átomos isolados!")
            return
        
        # Verifica se todas as espécies têm energia
        missing = []
        for idx, _, _ in self.system_species:
            if idx not in self.atom_energies:
                missing.append(str(idx))
        
        if missing:
            messagebox.showerror("Erro", f"Faltam energias para as espécies: {', '.join(missing)}")
            return
        
        # Calcula energia de referência
        e_reference = 0.0
        details = []
        for idx, atomic_num, pseudo in self.system_species:
            symbol = re.sub(r'\..*$', '', pseudo)
            symbol = re.sub(r'[0-9]', '', symbol)
            count = self.species_counts.get(idx, 1)
            e_atom = self.atom_energies[idx]
            contribution = count * e_atom
            e_reference += contribution
            details.append(f"{count}×E({symbol})")
        
        # Energia de coesão
        e_coh = self.system_energy - e_reference
        e_coh_per_atom = e_coh / self.system_atoms if self.system_atoms > 0 else 0
        
        # Exibe resultados
        result = "=" * 70 + "\n"
        result += "RESULTADO DA ENERGIA DE COESÃO\n"
        result += "=" * 70 + "\n\n"
        
        result += f"Energia do sistema:        {self.system_energy:.8f} eV\n"
        result += f"Energia de referência:     {e_reference:.8f} eV\n"
        result += f"  ({' + '.join(details)})\n\n"
        
        result += f"Energia de coesão total:   {e_coh:.8f} eV\n"
        result += f"Energia de coesão/átomo:   {e_coh_per_atom:.8f} eV/átomo\n\n"
        
        if e_coh_per_atom < 0:
            result += "✓ SISTEMA ESTÁVEL (energia de coesão negativa)\n"
            if e_coh_per_atom < -5:
                result += "  Alta estabilidade\n"
            elif e_coh_per_atom < -3:
                result += "  Boa estabilidade\n"
            elif e_coh_per_atom < -1:
                result += "  Estabilidade moderada\n"
            else:
                result += "  Estabilidade baixa\n"
        else:
            result += "✗ SISTEMA INSTÁVEL (energia de coesão positiva)\n"
        
        result += "=" * 70 + "\n"
        
        self.result_text.config(state='normal')
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(1.0, result)
        self.result_text.config(state='disabled')
        
        self.log(f"Cálculo concluído: E_coh = {e_coh_per_atom:.6f} eV/átomo", "INFO")
    
    def save_results(self):
        """Salva os resultados"""
        content = self.result_text.get(1.0, tk.END).strip()
        if not content:
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de texto", "*.txt"), ("Todos", "*.*")]
        )
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(content)
            self.log(f"Resultados salvos em: {os.path.basename(filepath)}", "INFO")
    
    def clear_all(self):
        """Limpa todos os dados"""
        self.system_file = None
        self.system_energy = None
        self.system_atoms = 0
        self.system_species = []
        self.species_counts = {}
        self.atom_energies = {}
        self.atom_files = {}
        
        for widget in self.atom_controls.winfo_children():
            widget.destroy()
        
        self.sys_label.config(text="Nenhum arquivo", foreground="gray")
        
        for text_widget in [self.sys_info, self.atom_info, self.result_text]:
            text_widget.config(state='normal')
            text_widget.delete(1.0, tk.END)
            text_widget.config(state='disabled')
    
    def log(self, message, level="INFO"):
        """Adiciona mensagem ao log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

def main():
    root = tk.Tk()
    app = CohesiveEnergyCalculator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
