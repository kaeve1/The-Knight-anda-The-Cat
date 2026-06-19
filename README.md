# The Knight and the Cat 🐱⚔️

Demo de jogo 2D desenvolvido em **Python + Pygame** como Atividade Prática da
disciplina **Linguagem de Programação Aplicada** (UNINTER — Prof. Jadson de
Araujo Almeida, 2026).

Um cavaleiro sai em busca do seu gato, que desapareceu pelo reino. No caminho
ele enfrenta hordas de esqueletos e, ao final, uma serpente gigante que guarda
o paradeiro do bichano.

---

## 🎮 Sobre o jogo

| | |
|---|---|
| **Gênero** | Ação 2D / Beat 'em up de rolagem lateral |
| **Engine / Lib** | [Pygame](https://www.pygame.org/) |
| **Resolução** | 576×324 (pixel art) |
| **Fases** | Fase 1 — ondas de esqueletos · Fase 2 — sala do boss (serpente) |

### Controle do jogador
- **A / D** — Mover (esquerda / direita)
- **W ou Espaço** — Pular
- **Clique esquerdo** — Atacar
- **Clique direito** — Defender (bloqueia dano enquanto segurado, parado no chão)

Esses comandos também aparecem na tela de **Opções** do próprio jogo.

### Desafio
Ao longo da Fase 1 o jogador enfrenta ondas de inimigos esqueletos (arqueiro,
lanceiro e guerreiro, cada um com padrão de ataque e alcance próprios). Ao
vencer todas as ondas, o gato aparece e foge para a Fase 2, onde o jogador
encara a **BossSnake**, um chefe com ataques normais e um ataque especial.

### Condição de vitória
Derrotar o boss na Fase 2 e alcançar o gato resgatado encerra o jogo com a
tela de vitória (**WIN**).

### Condição de derrota
Se o HP do cavaleiro/gato chegar a zero (em qualquer uma das fases), a partida
termina na tela de **GAME OVER**.

### Dificuldades
O menu de Opções permite escolher entre dois modos, cada um com um conjunto de
vidas e regras de dano diferente:

| Modo | Vidas | Dano recebido | Cura |
|---|---|---|---|
| 🐈 **Cat (Easy)** | 7 | Sempre limitado a 1 de dano | +1 coração a cada onda vencida |
| 🛡️ **Knight (Hard)** | 3 | Dano normal | Só cura ao chegar na sala do boss |

### Outras features
- **Sistema de pontuação** com persistência local em SQLite
  (`data/scores.db`), salvando pontuação, dificuldade e data ao final de cada
  partida.
- **Tela de Recordes (Records)**, exibindo o ranking das melhores pontuações.
- Ganho de pontos durante a fase concede vidas extras ao atingir certos
  marcos de score.
- HUD com corações pixel art representando o HP atual.
- Efeitos visuais retrô: scanlines, vinheta e bordas estilo CRT.

---

## 🗂️ Estrutura do projeto

```
ProjectGame/
├── ProjectGame.exe          # Executável Windows (build final)
└── _internal/
    ├── code/                 # Código-fonte do jogo
    │   ├── Game.py           # Loop principal / orquestra menu e fases
    │   ├── Menu.py           # Tela de menu inicial
    │   ├── Options.py        # Tela de opções (dificuldade + controles)
    │   ├── ScoreBoard.py     # Tela de recordes
    │   ├── Level.py          # Fase 1 (ondas de esqueletos)
    │   ├── Level2.py         # Fase 2 (sala do boss)
    │   ├── Player.py         # Lógica e animações do jogador
    │   ├── Enemy.py          # Inimigos esqueleto (arqueiro/lanceiro/guerreiro)
    │   ├── BossSnake.py      # Chefe final
    │   ├── Entity.py / EntityFactory.py
    │   ├── Background.py     # Parallax / cenário
    │   ├── Score.py          # Pontuação da sessão + persistência SQLite
    │   ├── Const.py          # Constantes globais (resolução, opções de menu)
    │   └── Settings.py       # Dificuldade selecionada
    ├── assets/               # Sprites, sons, fontes e backgrounds
    │   ├── knight/ cat/ skeleton/ boss/   # Spritesheets dos personagens
    │   ├── level1_background/ level2/     # Cenários
    │   ├── music/                          # Trilha sonora (.mp3)
    │   └── font/                           # Fonte pixel (Cardinal.ttf)
    └── data/
        └── scores.db          # Banco SQLite com o histórico de pontuações
```

> Todos os caminhos de assets no código usam **caminho relativo**
> (ex.: `./assets/knight/...`), conforme orientado na atividade, garantindo
> que o projeto funcione em qualquer máquina sem depender da estrutura de
> pastas do computador onde foi desenvolvido.

---

## ▶️ Como jogar

### Opção 1 — Executável (Windows)
1. Extraia o `.zip` mantendo a hierarquia de pastas intacta (o `.exe`
   precisa estar na mesma pasta que `_internal/`).
2. Execute `ProjectGame.exe`.

> Caso o executável feche sozinho ou apresente erro, rode-o via **CMD** para
> visualizar a mensagem de erro gerada (ex.: `ProjectGame.exe` digitado
> dentro do prompt de comando na pasta correspondente).

### Opção 2 — Código-fonte (Python)
Pré-requisitos: Python 3.13+ e a biblioteca `pygame`.

```bash
pip install pygame
cd ProjectGame/_internal
python -m code.Game   # ou o script de entrada equivalente do projeto
```

- ✅ Condição de vitória (derrotar o boss e resgatar o gato)
- ✅ Condição de derrota (Game Over ao zerar o HP)
- ✅ Menu inicial com os comandos de controle listados (tela de Opções)
- ✅ Build compilada para Windows (`.exe` + assets) entregue em `.zip`
