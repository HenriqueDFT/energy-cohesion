

# Energy Cohesion - Calculadora de Energia de Coesão para SIESTA

[![Versão Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Licença: MIT](https://img.shields.io/badge/Licença-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Plataforma](https://img.shields.io/badge/plataforma-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)](https://github.com/)

Uma interface gráfica robusta e amigável para calcular **energia de coesão** a partir de cálculos DFT com o SIESTA. Esta ferramenta extrai automaticamente energias totais e informações de espécies atômicas dos arquivos de saída (.out) do SIESTA para calcular energias de coesão por átomo.

## ✨ Funcionalidades

- **GUI Intuitiva** - Desenvolvida com Tkinter para fácil uso multiplataforma
- **Detecção Automática de Espécies** - Lê o bloco `ChemicalSpeciesLabel` do arquivo de saída do SIESTA
- **Contagem Precisa de Átomos** - Extrai quantidades do bloco `AtomicCoordinatesAndAtomicSpecies`
- **Processamento em Lote** - Carregue múltiplos arquivos de átomos isolados para diferentes espécies
- **Resultados Abrangentes** - Exibe energia de coesão total e por átomo
- **Avaliação de Estabilidade** - Classifica automaticamente a estabilidade do sistema
- **Exportação de Resultados** - Salve cálculos em arquivos de texto para documentação
- **Interface Organizada** - Layout com scroll para seções de sistema, átomos e resultados

## 📐 Equação e Fundamentos Teóricos

### Fórmula Fundamental

A energia de coesão é calculada pela seguinte equação:

$$
E_{coh} = E_{sistema} - \sum_{i=1}^{N} n_i \cdot E_{átomo}^{(i)}
$$

#### Onde cada termo representa:

**🔹 E_cohesão (Energia de Coesão Total)**
- **Definição**: Energia necessária para separar o sistema sólido em átomos isolados
- **Unidade**: eV (elétron-volt)
- **Interpretação**: 
  - Negativa → sistema estável (liberou energia ao se formar)
  - Positiva → sistema instável (requer energia para se manter)
  - Quanto mais negativa, mais forte é a ligação química

**🔹 E_sistema (Energia Total do Sistema)**
- **Definição**: Energia total do sistema bulk calculada pelo SIESTA
- **Obtida de**: Linha `siesta: Etot = X.XXXXXX eV` no arquivo `.out`
- **Inclui**: Todas as interações eletrônicas, nucleares e de troca-correlação

**🔹 Σ (Somatório)**
- **Definição**: Soma sobre todas as espécies químicas presentes no sistema
- **N**: Número total de espécies diferentes

**🔹 n_i (Número de Átomos da Espécie i)**
- **Definição**: Quantidade de átomos da espécie i no sistema
- **Obtida de**: Bloco `%block AtomicCoordinatesAndAtomicSpecies` no `.out`
- **Exemplo**: Em Si₂C₁, n_Si = 2 e n_C = 1

**🔹 E_átomo^(i) (Energia do Átomo Isolado)**
- **Definição**: Energia total de um único átomo da espécie i em estado isolado
- **Obtida de**: Arquivo `.out` do cálculo do átomo isolado
- **Observação**: Deve ser calculado com os mesmos parâmetros do sistema

### Energia de Coesão por Átomo

Para comparar diferentes sistemas, normalizamos pelo número total de átomos:

$$
E_{coh}^{por\;átomo} = \frac{E_{coh}}{N_{total}}
$$

Onde:

$$
N_{total} = \sum_{i=1}^{N} n_i
$$

**Unidade**: eV/átomo
### Considerações e Limitações

#### 1. Consistência dos Cálculos
Para resultados confiáveis, **todos os cálculos** (sistema e átomos isolados) devem usar:
- Mesmo funcional de troca-correlação (ex: PBE, LDA)
- Mesmo conjunto de base (ex: DZP, TZP)
- Mesmo cutoff de energia
- Mesmo pseudopotencial

#### 2. Correções Adicionais
Em cálculos mais avançados, podem ser incluídas correções:
- **Correção de BSSE** (Basis Set Superposition Error)
- **Correção de Spin** (para sistemas com spin polarizado)
- **Correção de Dispersão** (DFT-D)

#### 3. Limitações da Fórmula
A fórmula assume que:
- **Átomos isolados estão em estado fundamental** - O cálculo do átomo deve estar bem convergido
- **Não há interações entre átomos isolados** - Cada átomo é tratado independentemente
- **O sistema é bem convergido energeticamente** - Critérios de convergência rigorosos devem ser aplicados
- **Efeitos de tamanho de caixa são desprezíveis** - Para átomos isolados, a caixa deve ser suficientemente grande

### Implementação no Software

No código do **Energy Cohesion**, a equação é implementada como:

```python
# Cálculo da energia de referência
e_reference = 0.0
for idx, atomic_num, pseudo in self.system_species:
    count = self.species_counts.get(idx, 1)
    e_atom = self.atom_energies[idx]
    contribution = count * e_atom
    e_reference += contribution

# Energia de coesão total
e_coh = self.system_energy - e_reference

# Energia de coesão por átomo
e_coh_per_atom = e_coh / self.system_atoms



```
### Considerações e Limitações

1. **Consistência dos Cálculos**:
   Para garantir a precisão dos resultados, **todos os cálculos** (sistema e átomos isolados) devem ser configurados com parâmetros idênticos:
   - Mesmo funcional de troca-correlação (ex: PBE, LDA)
   - Mesmo conjunto de base (ex: DZP, TZP)
   - Mesmo *cutoff* de energia (*MeshCutoff*)
   - Mesmos pseudopotenciais

2. **Correções Adicionais**:
   Dependendo da precisão desejada, correções externas podem ser necessárias:
   - **BSSE** (*Basis Set Superposition Error*)
   - **Correção de Spin** (essencial para átomos isolados com momento magnético não nulo)
   - **Correção de Dispersão/Van der Waals** (ex: DFT-D)

3. **Premissas da Fórmula**:
   - Os átomos isolados são calculados em uma caixa suficientemente grande para evitar interações entre imagens periódicas.
   - O cálculo do átomo isolado deve refletir o seu estado fundamental eletrônico.

---

### Implementação no Software

A lógica de cálculo central do **Energy Cohesion** é executada conforme o trecho abaixo:

```python
# Cálculo da energia de referência (soma das energias dos átomos isolados)
e_reference = 0.0
for idx, atomic_num, pseudo in self.system_species:
    count = self.species_counts.get(idx, 1)
    e_atom = self.atom_energies[idx]
    contribution = count * e_atom
    e_reference += contribution

# Energia de coesão total
e_coh = self.system_energy - e_reference

# Energia de coesão por átomo
e_coh_per_atom = e_coh / self.system_atoms
```

---

## 🔬 Fundamentos Científicos e Aplicações

A energia de coesão é uma propriedade físico-química fundamental para a caracterização de materiais sólidos e moleculares. Ela mede diretamente a intensidade das forças de coesão (ligações covalentes, iônicas, metálicas ou forças de Van der Waals) que mantêm os átomos unidos.

### Aplicações Típicas:
- **Descoberta e Screening de Materiais**: Comparação da estabilidade relativa de diferentes polimorfos e fases cristalinas.
- **Cálculos de Defectos e Ligas**: Base para determinar energias de formação de vacâncias, substituições e energias de mistura em ligas metálicas.
- **Ciência de Superfícies e Nanoestruturas**: Avaliação da estabilidade de filmes finos, estruturas 2D, e energias de clivagem/superfície.

### Especificidades do SIESTA
O código [SIESTA](https://materia.ciencias.unam.mx/siesta/) (*Spanish Initiative for Electronic Simulations with Thousands of Atoms*) utiliza orbitais atômicos localizados de raio finito como função de base, tornando o rigor na escolha da caixa de simulação e na convergência de energia crucial para cálculos precisos de átomos isolados.

---

## 🚀 Instalação e Execução

### Pré-requisitos
- **Python 3.8** ou superior
- **Tkinter** (geralmente pré-instalado com as distribuições padrão do Python)

### Clonar o Repositório
```bash
git clone [https://github.com/HenriqueDFT/energy-cohesion.git](https://github.com/HenriqueDFT/energy-cohesion.git)
cd energy-cohesion
```

### Execução
Nenhuma biblioteca externa adicional é necessária. Para iniciar a interface, execute:

```bash
python coesin.py
```

#### Módulos da Biblioteca Padrão Utilizados:
- `tkinter`: Construção da Interface Gráfica de Usuário (GUI)
- `re`: Parseamento via Expressões Regulares dos arquivos do SIESTA
- `os`: Manipulação de caminhos e arquivos do sistema operacional
- `datetime`: Registro de datas e timestamps para os relatórios
- `threading`: Execução assíncrona em segundo plano para manter a GUI responsiva

---

## 🤝 Como Contribuir

Contribuições são extremamente bem-vindas! Sinta-se à vontade para colaborar com o projeto das seguintes maneiras:

1. **Reportar Bugs**: Abra uma *Issue* detalhando o problema, incluindo o erro e, se possível, os arquivos `.out` que geraram a falha.
2. **Sugerir Funcionalidades**: Ideias para novas métricas ou melhorias de UX/UI são sempre bem-vindas.
3. **Enviar Pull Requests**:
   - Faça um *Fork* do repositório
   - Crie uma *Branch* com a sua modificação (`git checkout -b feature/NovaFuncionalidade`)
   - Submeta o *Pull Request* para revisão
4. **Documentação**: Sugira melhorias no guia de usuário, explicações teóricas ou adição de exemplos práticos.

# 🔍 Conheça o grupo de nanofísica computacional(GNC)
'https://www.instagram.com/nanofisica/'

## 🧑‍💻 Autor

Desenvolvido por Henrique Lago, bacharel em Física pela Universidade Federal do Piauí (UFPI), membro do grupo de Nanofísica Computacional (GNC/UFPI), com experiência em simulações via DFT utilizando o pacote SIESTA.

GitHub: @HenriqueDFT

---

## 📜 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).
Veja o arquivo `LICENSE` para mais detalhes.

    
