"""Apply Martial Maneuvers Remaster to wiki pages and classes.

Creates the new 'manobras-marciais' page under category 'rules', updates all classes,
subclasses, invocations, and spells, and updates 'novas-opcoes-de-ataque'.
"""
import os
import sys
import re

# Setup Django environment
sys.path.insert(0, os.path.abspath('backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'compendium.settings')

import django
django.setup()

from django.db import transaction
from wiki.models import Page, Category, Tag
from wiki.services import save_page_with_derived_data

def get_or_create_rules_category():
    rules_cat = Category.objects.filter(slug='rules').first()
    if not rules_cat:
        rules_cat = Category.objects.create(
            name='Rules',
            slug='rules',
            sidebar_group='core',
            in_sidebar=True
        )
    return rules_cat

MANOBRAS_MARCIAIS_CONTENT = """Esse remaster visa readaptar o sistema de D&D para redefinir o poder de um personagem marcial em sua própria capacidade, e não nos seus equipamentos mágicos.

### O Problema do Ataque Extra (Extra Attack)
O sistema tradicional de D&D é baseado estruturalmente no ataque extra, o que faz personagens marciais ficarem excessivamente dependentes de armas mágicas por receberem o efeito de dano da arma várias vezes no mesmo turno. Por conta disso, todos os marciais acabam sendo nivelados para baixo para não desequilibrarem com armas mágicas.

### A Solução
A proposta deste remaster é dar mais versatilidade, escolhas táticas dinâmicas e uma progressão consistente para os marciais, em troca de mais profundidade no combate.

---

## Regra Geral: Extra-Attack > Manobras Marciais (Martial Maneuvers)

Quando você recebe o recurso **Extra Attack** (*Ataque Extra*), seja pela sua classe, subclasse ou por algum feitiço, você agora recebe em seu lugar o recurso **Manobras Marciais** (*Martial Maneuvers*).

### Como Funciona
- **Escolha de Manobras:** Ao receber acesso a esse recurso, você escolhe um número de manobras indicado pela sua classe, subclasse ou feitiço.
- **Troca de Manobras:** Você não pode alterar suas manobras, exceto se receber o recurso por **classe** (podendo alterar uma manobra sempre que finalizar um descanso longo) ou por subclasse quando indicado na descrição (podendo alterar uma ao subir de nível na classe).
- **Uso em Combate:** Quando utilizar sua ação de **Ataque**, você pode usar uma das manobras marciais às quais tem acesso.
- **Ataque Extra como Manobra:** O ataque adicional tradicional passa a ser a manobra [Ataque Extra](#ataque-extra), disponível para quase todas as classes marciais.
- **Salvaguardas das Manobras:** Quando uma manobra exigir um teste de resistência do alvo, a dificuldade é:
  $$\\text{CD da Salvaguarda} = 8 + \\text{Bônus de Proficiência} + \\text{Modificador de Força ou Destreza (ou atributo de conjuração se aplicável)}$$

---

## Superioridade e Dado de Superioridade

Conforme você evolui na sua classe, você melhora suas capacidades de infligir dano. Cada classe possui um **dado de superioridade** representando sua maestria marcial, que evolui conforme avança de forma semelhante aos *spell slots* dos conjuradores.

O dado evolui de acordo com a sua classificação marcial:
- **Full Marciais:** 1 nível marcial a cada nível de classe.
- **Half-Marciais:** 1 nível marcial a cada dois níveis de classe (arredondado para baixo).
- **Third-Marciais:** 1 nível marcial a cada três níveis de classe (arredondado para baixo).

### Tabela Mestra de Nível Marcial x Dado de Superioridade

| Nível Marcial | Dado de Superioridade |
| :---: | :---: |
| **1** | d4 |
| **2** | d4 |
| **3** | d4 |
| **4** | d4 |
| **5** | d4 |
| **6** | d6 |
| **7** | d6 |
| **8** | d6 |
| **9** | d6 |
| **10** | d8 |
| **11** | d8 |
| **12** | d8 |
| **13** | d8 |
| **14** | d10 |
| **15** | d10 |
| **16** | d10 |
| **17** | d10 |
| **18** | d12 |
| **19** | d12 |
| **20** | d12 |

---

## Regras e Progressão por Classe

### Full Marciais
**Classes:** [Guerreiro (Fighter)](/classes/fighter), [Bárbaro (Barbarian)](/classes/barbarian), [Monge (Monk)](/classes/monk), [Witcher](/classes/witcher).

- **Aquisição:** No nível 5 você aprende a realizar manobras marciais.
- **Dado de Superioridade:** Começa em **d4** no nível 5. Aumenta para **d6** no nível 6, **d8** no nível 10, **d10** no nível 14 e **d12** no nível 18.
- **Manobras Conhecidas:** Você conhece um número de manobras igual a **2 + seu bônus de proficiência**.
- **Troca:** Pode alterar uma manobra sempre que finalizar um descanso longo.

| Nível de Classe | Nível Marcial | Dado de Superioridade | Manobras Conhecidas |
| :---: | :---: | :---: | :---: |
| 5 | 5 | d4 | 5 (2 + 3) |
| 6–8 | 6–8 | d6 | 5 (2 + 3) |
| 9–12 | 9–12 | d6 (9) / d8 (10–12) | 6 (2 + 4) |
| 13–16 | 13–16 | d8 (13) / d10 (14–16) | 7 (2 + 5) |
| 17–20 | 17–20 | d10 (17) / d12 (18–20) | 8 (2 + 6) |

---

### Half-Marciais
**Classes:** [Herói](/classes/heroi), [Ranger / Patrulheiro](/classes/ranger), [Paladino](/classes/paladin), [Filho da Magia (Magic Born)](/classes/filho-da-magia), [Cavaleiro da Morte](/classes/cavaleiro-da-morte), [Caçador de Demônios (Demon Hunter)](/classes/cacador-de-demonios), [Dovahkiin](/classes/dovahkiin).

- **Aquisição:** No nível 5 você aprende a realizar manobras marciais.
- **Dado de Superioridade:** Começa em **d4** no nível 5. No nível 12 torna-se **d6** e no nível 20 torna-se **d8** (calculado por $\\lfloor \\text{Nível de Classe} / 2 \\rfloor$).
- **Manobras Conhecidas:** Você conhece um número de manobras igual ao seu **modificador de conjuração, Força ou Destreza (o que for maior)**.
- **Troca:** Pode alterar uma manobra sempre que finalizar um descanso longo.

| Nível de Classe | Nível Marcial Efetivo | Dado de Superioridade |
| :---: | :---: | :---: |
| 5–11 | 2–5 | d4 |
| 12–19 | 6–9 | d6 |
| 20 | 10 | d8 |

---

### Third-Marciais e Subclasses

#### Artificer (Battle Smith / Armorer / Cosmic Tinker)
- **Aquisição:** No nível 5 você aprende a realizar manobras marciais.
- **Dado de Superioridade:** **d4** no nível 5; torna-se **d6** no nível 12 e **d8** no nível 20.
- **Manobras Conhecidas:** Igual ao seu modificador de **Inteligência**.
- **Troca:** Pode alterar uma manobra sempre que ganhar um novo nível nesta classe.
- **Manobras Disponíveis:** [Isca e Troca](#isca-e-troca), [Apostar](#apostar), [Ataque Distrativo](#ataque-distrativo), [Ataque Extra](#ataque-extra), [Ataque de Manobra](#ataque-de-manobra), [Expelir Magia](#expelir-magia), [Ataque em Avanço](#ataque-em-avanco) *(apenas Battle Smith)*, [Cortar Tendões](#cortar-tendoes), [Ataque de Confusão](#ataque-de-confusao).

#### Bardo (Colégio do Valor / College of Valor)
- **Aquisição:** No nível 6 você aprende a realizar manobras marciais.
- **Dado de Superioridade:** **d4** no nível 6; torna-se **d6** no nível 18.
- **Manobras Conhecidas:** Igual ao seu modificador de **Carisma**.
- **Troca:** Pode alterar uma manobra sempre que ganhar um novo nível nesta classe.
- **Manobras Disponíveis:** [Emboscada](#emboscada), [Isca e Troca](#isca-e-troca), [Apostar](#apostar), [Ataque Distrativo](#ataque-distrativo), [Ataque Extra](#ataque-extra) *(pode substituir um ataque por um truque/cantrip)*, [Ataque Desarmante](#ataque-desarmante), [Expelir Magia](#expelir-magia), [Ataque em Avanço](#ataque-em-avanco), [Ataque Desnorteante](#ataque-desnorteante).

#### Mago (Bladesinger / Lâmina Cantante)
- **Aquisição:** No nível 6 você aprende a realizar manobras marciais.
- **Dado de Superioridade:** **d4** no nível 6; torna-se **d6** no nível 18.
- **Manobras Conhecidas:** Igual ao seu modificador de **Inteligência**.
- **Troca:** Pode alterar uma manobra sempre que ganhar um novo nível nesta classe.
- **Manobras Disponíveis:** [Emboscada](#emboscada), [Ataque Desarmante](#ataque-desarmante), [Ataque Extra](#ataque-extra) *(pode substituir um ataque por um truque/cantrip)*, [Ataque de Manobra](#ataque-de-manobra), [Ataque em Avanço](#ataque-em-avanco), [Ataque Rasteira](#ataque-rasteira), [Expelir Magia](#expelir-magia).

#### Bruxo (Pacto da Lâmina - Thirsting Blade)
- **Aquisição:** Ao escolher a invocação *Thirsting Blade* (disponível no nível 5+), você aprende a realizar manobras marciais com sua arma do pacto.
- **Dado de Superioridade:** **d4**; torna-se **d6** no nível 18.
- **Manobras Conhecidas:** Igual ao seu modificador de **Carisma**.
- **Troca:** Pode alterar uma manobra sempre que ganhar um novo nível nesta classe.
- **Manobras Disponíveis:** [Emboscada](#emboscada), [Ataque Agarrador](#ataque-agarrador), [Ataque Distrativo](#ataque-distrativo), [Ataque Extra](#ataque-extra) *(pode substituir um ataque por um truque/cantrip)*, [Ataque Desarmante](#ataque-desarmante), [Arremesso Rápido](#arremesso-rapido), [Expelir Magia](#expelir-magia), [Ataque em Avanço](#ataque-em-avanco), [Ataque Varredura](#ataque-varredura), [Ataque Desnorteante](#ataque-desnorteante), [Abate](#abate), [Cortar Tendões](#cortar-tendoes), [Onda de Choque](#onda-de-choque).

---

## Feitiços Adaptados

### [Haste (Velocidade)](/spells/haste)
Escolha uma criatura voluntária que você possa ver dentro do alcance. Até a magia terminar, o Deslocamento do alvo é dobrado, ele recebe um bônus de +2 na Classe de Armadura, tem Vantagem em testes de resistência de Destreza e ganha uma ação adicional em cada um dos seus turnos. Essa ação pode ser usada apenas para realizar a ação Atacar (**Não pode usar manobras nesse ataque**), Disparar, Desengajar, Esconder-se ou Utilizar. Quando a magia termina, o alvo fica Incapacitado e tem Deslocamento 0 até o final do seu próximo turno, conforme uma onda de letargia o consome.

### [Tasha's Otherworldly Guise](/spells/tashas-otherworldly-guise)
Ao proferir um encantamento, você canaliza a magia dos Planos Inferiores ou dos Planos Superiores (à sua escolha) para se transformar. Você recebe os seguintes benefícios até a magia terminar:
- Imunidade a dano de fogo e de veneno (Planos Inferiores) ou a dano radiante e necrótico (Planos Superiores).
- Imunidade à condição envenenado (Planos Inferiores) ou à condição enfeitiçado (Planos Superiores).
- Asas espectrais surgem nas suas costas, concedendo um deslocamento de voo de 12 metros (40 pés).
- Bônus de +2 na Classe de Armadura (CA).
- Todos os seus ataques com arma são mágicos e você pode usar o modificador da sua habilidade de conjuração em vez de Força ou Destreza para jogadas de ataque e dano.
- Capacidade de usar as seguintes Manobras Marciais com dado de superioridade **d4**: [Ataque Extra](#ataque-extra), [Ataque Desarmante](#ataque-desarmante), [Expelir Magia](#expelir-magia), [Ataque em Avanço](#ataque-em-avanco).

### [Tenser’s Transformation (Transformação de Tenser)](/spells/tensers-transformation)
Você se reveste de vigor e proeza marcial alimentados por magia. Até a magia terminar, você não pode conjurar magias e ganha os seguintes benefícios:
- 50 pontos de vida temporários.
- Vantagem nas jogadas de ataque com armas simples e marciais.
- 2d12 de dano de energia adicional ao atingir com ataque com arma.
- Proficiência com todas as armaduras, escudos, armas simples e armas marciais.
- Proficiência em salvaguardas de Força e Constituição.
- Capacidade de usar as seguintes Manobras Marciais com dado de superioridade **d4**: [Ataque Extra](#ataque-extra), [Ataque de Empurrão](#ataque-de-empurrao), [Expelir Magia](#expelir-magia), [Ataque Varredura](#ataque-varredura).
- Ao término, salvaguarda de Constituição CD 15 ou sofre um nível de exaustão.

---

## Matriz de Manobras por Classe

| Manobra | Guerreiro | Bárbaro | Monge | Witcher | Ranger | Paladino | Herói | F. Magia | C. Morte | C. Demônios | Dovahkiin |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Emboscada** | ✔ | ✔ | ✔ | ✔ | ✔ | | | | | ✔ | ✔ |
| **Isca e Troca** | ✔ | | | ✔ | ✔ | ✔ | ✔ | | ✔ | ✔ | |
| **Apostar** | ✔ | | ✔ | | ✔ | | ✔ | ✔ | | | ✔ |
| **Ataque Desarmante** | ✔ | | ✔ | ✔ | | ✔ | | ✔ | ✔ | | |
| **Ataque Distrativo** | ✔ | | ✔ | | | | ✔ | ✔ | | ✔ | ✔ |
| **Ataque Extra** | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| **Ataque Agarrador** | ✔ | ✔ | | ✔ | ✔ | ✔ | ✔ | | ✔ | ✔ | ✔ |
| **Ataque em Avanço** | | ✔ | ✔ | | ✔ | | | ✔ | | ✔ | |
| **Ataque Desnorteante** | ✔ | | ✔ | | ✔ | | | ✔ | | ✔ | ✔ |
| **Abate** | ✔ | | | | | | | | ✔ | | ✔ |
| **Ataque de Manobra** | ✔ | | | | | ✔ | ✔ | | ✔ | | ✔ |
| **Ataque de Empurrão** | ✔ | ✔ | ✔ | | ✔ | ✔ | | | ✔ | | ✔ |
| **Arremesso Rápido** | ✔ | | ✔ | | ✔ | | ✔ | ✔ | | ✔ | |
| **Ataque Varredura** | ✔ | ✔ | | | | ✔ | ✔ | ✔ | ✔ | | ✔ |
| **Ataque Rasteira** | ✔ | | ✔ | ✔ | ✔ | | ✔ | ✔ | | ✔ | |
| **Expelir Magia** | | | | | ✔ | ✔ | ✔ | ✔ | | ✔ | ✔ |
| **Brutalizar** | | ✔ | | | | | | | | | |
| **Ataque Atordoante** | | | ✔ | | | | | | | | |
| **Ataque com Sinal** | | | | ✔ | | | | | | | |
| **Ataque da Morte** | | | | | | | | | ✔ | | |
| **Abrir Defesas** | ✔ | | | | | ✔ | ✔ | ✔ | ✔ | | ✔ |
| **Cortar Tendões** | ✔ | ✔ | | ✔ | | | | | ✔ | ✔ | ✔ |
| **Ataque de Confusão** | ✔ | ✔ | ✔ | ✔ | ✔ | | ✔ | | | | ✔ |
| **Causar Feridas** | ✔ | ✔ | | ✔ | | | | ✔ | ✔ | ✔ | |
| **Onda de Choque** | ✔ | ✔ | | | | ✔ | ✔ | ✔ | | ✔ | |

---

## Lista Completa de Manobras Marciais

### Emboscada
**Classes Autorizadas:** Guerreiro, Bárbaro, Witcher, Ranger, Caçador de Demônios, Dovahkiin, Monge *(além de Bardo do Valor, Bladesinger e Bruxo Thirsting Blade)*.  
Quando rolar iniciativa e não estiver surpreso, você pode andar metade do seu movimento e usar sua ação de Ataque antes que qualquer um aja. O resto de sua ação deve ser feito normalmente quando chegar a sua vez na rodada. Se o ataque atingir, adicione o dado de superioridade à jogada de dano da arma.

### Isca e Troca
**Classes Autorizadas:** Guerreiro, Witcher, Ranger, Caçador de Demônios, Cavaleiro da Morte, Herói, Paladino *(além de Artificer e Bardo do Valor)*.  
Quando você estiver a até 1,5 metro de uma criatura no seu turno, você pode trocar de lugar com ela, desde que gaste pelo menos 1,5 metro de movimento e a criatura esteja disposta e não incapacitada. Esse movimento não provoca ataques de oportunidade.  
Role o dado de superioridade. Até o início do seu próximo turno, você ou a outra criatura (sua escolha) ganha um bônus na CA igual ao número rolado.

### Apostar
**Classes Autorizadas:** Guerreiro, Ranger, Herói, Dovahkiin, Filho da Magia, Monge *(além de Artificer e Bardo do Valor)*.  
Quando uma criatura que você possa ver entrar no alcance da arma corpo a corpo que você está empunhando e você não tiver agido ainda, você pode usar sua ação de ataque contra a criatura usando essa arma. Se o ataque atingir, adicione o dado de superioridade à jogada de dano da arma. O resto de sua ação deve ser feito normalmente quando chegar a sua vez na rodada.

### Ataque Desarmante
**Classes Autorizadas:** Guerreiro, Witcher, Cavaleiro da Morte, Paladino, Filho da Magia, Monge *(além de Bardo do Valor, Bladesinger, Bruxo Thirsting Blade e Tasha's Otherworldly Guise)*.  
Quando você atingir uma criatura com um ataque com arma, você pode tentar desarmar o alvo, forçando-o a soltar um item à sua escolha que ele esteja segurando. Você adiciona o dado de superioridade à jogada de dano do ataque, e o alvo deve fazer um teste de resistência de Força. Se falhar, ele solta o objeto escolhido, que cai aos seus pés.

### Ataque Distrativo
**Classes Autorizadas:** Guerreiro, Dovahkiin, Caçador de Demônios, Herói, Filho da Magia, Monge *(além de Artificer, Bardo do Valor e Bruxo Thirsting Blade)*.  
Quando você atingir uma criatura com um ataque com arma, você pode distraí-la, dando uma abertura aos seus aliados. Você adiciona o dado de superioridade à jogada de dano do ataque. A próxima jogada de ataque contra o alvo feita por outro atacante além de você terá vantagem se for realizada antes do início do seu próximo turno.

### Ataque Extra
**Classes Autorizadas:** Guerreiro, Witcher, Ranger, Caçador de Demônios, Cavaleiro da Morte, Herói, Paladino, Filho da Magia, Dovahkiin, Bárbaro, Monge *(além de Artificer, Bardo do Valor, Bladesinger, Bruxo Thirsting Blade, Tasha's Otherworldly Guise e Tenser’s Transformation)*.  
Quando realizar a ação de Ataque no seu turno, você pode realizar um ataque adicional.  
*Substituição por Cantrip:* Personagens com Bardo do Valor, Bladesinger ou Bruxo (Thirsting Blade) podem substituir um desses ataques por um truque (*cantrip*) com tempo de conjuração de 1 ação.

### Ataque Agarrador
**Classes Autorizadas:** Guerreiro, Witcher, Ranger, Caçador de Demônios, Cavaleiro da Morte, Herói, Paladino, Dovahkiin, Bárbaro *(além de Bruxo Thirsting Blade)*.  
Imediatamente após atingir uma criatura com um ataque corpo a corpo no seu turno, você pode tentar agarrar o alvo com uma ação bônus (consulte as regras de agarrar). Adicione o dado de superioridade ao seu teste de Força (Atletismo).

### Ataque em Avanço
**Classes Autorizadas:** Ranger, Caçador de Demônios, Filho da Magia, Bárbaro, Monge *(além de Artificer Battle Smith, Bardo do Valor, Bladesinger, Bruxo Thirsting Blade e Tasha's Otherworldly Guise)*.  
Quando você fizer um ataque com arma corpo a corpo no seu turno, pode aumentar o alcance desse ataque em 1,5 metro. Se atingir, adicione o dado de superioridade à jogada de dano do ataque.

### Ataque Desnorteante
**Classes Autorizadas:** Ranger, Caçador de Demônios, Filho da Magia, Dovahkiin, Monge, Guerreiro *(além de Bardo do Valor e Bruxo Thirsting Blade)*.  
Quando você atingir uma criatura com um ataque com arma, você pode forçá-la a perder a concentração imediatamente.

### Abate
**Classes Autorizadas:** Cavaleiro da Morte, Dovahkiin, Guerreiro *(além de Bruxo Thirsting Blade)*.  
Quando você atingir uma criatura com um ataque com arma e ela ficar com menos pontos de vida do que o seu nível de personagem, os pontos de vida dela zeram imediatamente.

### Ataque de Manobra
**Classes Autorizadas:** Guerreiro, Cavaleiro da Morte, Herói, Paladino, Dovahkiin *(além de Artificer e Bladesinger)*.  
Quando você atingir uma criatura com um ataque com arma, você pode manobrar um de seus companheiros para uma posição mais vantajosa. Você adiciona o dado de superioridade à jogada de dano do ataque e escolhe uma criatura aliada que possa ver ou ouvir você. Essa criatura pode usar a reação dela para se mover até a metade do seu deslocamento sem provocar ataques de oportunidade do alvo do seu ataque.

### Ataque de Empurrão
**Classes Autorizadas:** Guerreiro, Ranger, Cavaleiro da Morte, Paladino, Dovahkiin, Bárbaro, Monge *(além de Tenser’s Transformation)*.  
Quando você atingir uma criatura com um ataque com arma, você pode empurrar o alvo. Você adiciona o dado de superioridade à jogada de dano do ataque e, se o alvo for de tamanho Grande ou menor, ele deve fazer um teste de resistência de Força. Se falhar, você empurra o alvo até 4,5 metros para longe de você.

### Arremesso Rápido
**Classes Autorizadas:** Guerreiro, Ranger, Caçador de Demônios, Herói, Filho da Magia, Monge *(além de Bruxo Thirsting Blade)*.  
Como uma ação bônus, você pode fazer um ataque à distância com uma arma que tenha a propriedade de arremesso. Você pode sacar a arma como parte desse ataque. Se atingir, adicione o dado de superioridade à jogada de dano da arma.

### Ataque Varredura
**Classes Autorizadas:** Guerreiro, Cavaleiro da Morte, Herói, Paladino, Filho da Magia, Dovahkiin, Bárbaro *(além de Bruxo Thirsting Blade e Tenser’s Transformation)*.  
Quando você atingir uma criatura com um ataque corpo a corpo com arma, você pode tentar causar dano a outra criatura com o mesmo ataque. Escolha outra criatura a até 1,5 metro do alvo original e ao seu alcance. Se a jogada de ataque original atingir a segunda criatura, ela recebe dano igual ao número rolado no seu dado de superioridade. O dano é do mesmo tipo causado pelo ataque original.

### Ataque Rasteira
**Classes Autorizadas:** Guerreiro, Witcher, Ranger, Caçador de Demônios, Herói, Filho da Magia, Monge *(além de Bladesinger)*.  
Quando você atingir uma criatura com um ataque com arma, você pode tentar derrubá-la. Você adiciona o dado de superioridade à jogada de dano do ataque e, se o alvo for de tamanho Grande ou menor, ele deve fazer um teste de resistência de Força. Se falhar, você derruba o alvo no chão (condição Caído / Prone).

### Expelir Magia
**Classes Autorizadas:** Ranger, Caçador de Demônios, Herói, Paladino, Filho da Magia, Dovahkiin *(além de Artificer, Bardo do Valor, Bladesinger, Bruxo Thirsting Blade, Tasha's Otherworldly Guise e Tenser’s Transformation)*.  
Quando você atingir uma criatura com um ataque com arma, você pode consumir um espaço de magia (*spell slot*) não utilizado para causar dano adicional igual a um número de dados de superioridade igual a **1 + nível do espaço de magia consumido**.

### Brutalizar
**Classes Autorizadas:** Bárbaro.  
Quando você atingir uma criatura com um ataque com arma, cause dano adicional igual a um número de dados de superioridade igual ao modificador do seu *Rage* (Fúria).

### Ataque Atordoante
**Classes Autorizadas:** Monge.  
Quando você atingir uma criatura com um ataque com arma, você pode interferir no fluxo de ki no corpo de um oponente. O alvo deve ser bem-sucedido em um teste de resistência de Constituição ou ficará atordoado (*Stunned*) até o final do seu próximo turno.

### Ataque com Sinal
**Classes Autorizadas:** Witcher.  
Quando você atingir uma criatura com um ataque com arma, você pode conjurar um sinal witcher como parte da mesma ação. Você adiciona o dado de superioridade à CD (DC) do seu sinal.

### Ataque da Morte
**Classes Autorizadas:** Cavaleiro da Morte.  
Quando você atingir uma criatura com um ataque com arma, você pode conjurar o Golpe da Morte com uma redução de 1 no custo de pontos rúnicos (mínimo 0).

### Abrir Defesas
**Classes Autorizadas:** Guerreiro, Cavaleiro da Morte, Herói, Paladino, Filho da Magia, Dovahkiin.  
Quando você atingir uma criatura com um ataque com arma, pode forçar o alvo a realizar um ataque de oportunidade em você com a reação dele. Adicione o dado de superioridade à jogada de dano da arma.

### Cortar Tendões
**Classes Autorizadas:** Guerreiro, Cavaleiro da Morte, Dovahkiin, Bárbaro, Caçador de Demônios, Witcher *(além de Artificer e Bruxo Thirsting Blade)*.  
Quando você atingir uma criatura com um ataque com arma, reduza a velocidade de deslocamento dele pela metade até o fim do seu próximo turno. Adicione o dado de superioridade à jogada de dano da arma.

### Ataque de Confusão
**Classes Autorizadas:** Guerreiro, Ranger, Dovahkiin, Bárbaro, Herói, Witcher, Monge *(além de Artificer)*.  
Quando você atingir uma criatura com um ataque com arma, você pode forçá-la a realizar um teste de resistência de Constituição. Se falhar, ela não pode conjurar feitiços até o fim do próximo turno. Adicione o dado de superioridade à jogada de dano da arma.

### Causar Feridas
**Classes Autorizadas:** Guerreiro, Cavaleiro da Morte, Bárbaro, Caçador de Demônios, Witcher, Filho da Magia.  
Quando você atingir uma criatura com um ataque com arma, você pode forçá-la a realizar um teste de resistência de Constituição. Se falhar, ela recebe dano contínuo igual ao seu dado de superioridade no início de seus turnos até obter um sucesso no teste.

### Onda de Choque
**Classes Autorizadas:** Guerreiro, Bárbaro, Caçador de Demônios, Filho da Magia, Paladino, Herói *(além de Bruxo Thirsting Blade)*.  
Quando você acertar uma superfície, você pode causar uma onda de choque aumentando a área do impacto para 10 ft (raio de 3 metros). A onda de choque causa dano a tudo na área ignorando apenas o dano base da sua arma.
"""

def apply_all():
    rules_cat = get_or_create_rules_category()
    spells_cat = Category.objects.filter(slug='spells').first()

    with transaction.atomic():
        print("1. Creating / Updating 'manobras-marciais' page...")
        manobras_page, created = Page.objects.get_or_create(
            slug='manobras-marciais',
            defaults={
                'title': 'Manobras Marciais',
                'category': rules_cat,
                'source': 'homebrew',
                'visibility': 'public',
                'source_content': MANOBRAS_MARCIAIS_CONTENT,
            }
        )
        if not created:
            manobras_page.title = 'Manobras Marciais'
            manobras_page.category = rules_cat
            manobras_page.source_content = MANOBRAS_MARCIAIS_CONTENT
        save_page_with_derived_data(manobras_page, tag_names=['regras', 'manobras', 'combate', 'homebrew'])
        print(f"   -> Page 'manobras-marciais' saved successfully (created={created}).")

        print("2. Updating 'novas-opcoes-de-ataque' page...")
        noa_page = Page.objects.filter(slug='novas-opcoes-de-ataque').first()
        if noa_page:
            notice = (
                "> [!NOTE]\n"
                "> **Sistema Remasterizado:** Esta regra foi substituída pelo novo sistema de "
                "[Manobras Marciais](/rules/manobras-marciais) (Remaster de Weapon Attack), "
                "que unifica as opções de ataque e o dado de superioridade para todas as classes marciais.\n\n"
            )
            if not noa_page.source_content.startswith("> [!NOTE]"):
                noa_page.source_content = notice + noa_page.source_content
                save_page_with_derived_data(noa_page)
                print("   -> 'novas-opcoes-de-ataque' updated with remaster notice.")

        print("3. Updating Class: Fighter...")
        fighter = Page.objects.get(slug='fighter')
        # In table
        fighter.source_content = fighter.source_content.replace(
            "| 5 | +3 | Extra Attack, Tactical Shift | 3 | 4 |",
            "| 5 | +3 | Manobras Marciais (Martial Maneuvers), Tactical Shift | 3 | 4 |"
        )
        fighter_extra_attack_old = (
            "### Level 5: Extra Attack\n\n"
            "You can attack twice instead of once whenever you take the Attack action on your turn."
        )
        fighter_maneuvers_new = (
            "### Level 5: Manobras Marciais (Martial Maneuvers)\n\n"
            "*Substitui o Extra Attack.* No nível 5 você aprende a realizar [Manobras Marciais](/rules/manobras-marciais). "
            "Seu dado de superioridade inicial é **d4** e aumenta conforme ganha níveis nesta classe (**d6** no nível 6, "
            "**d8** no nível 10, **d10** no nível 14 e **d12** no nível 18).\n\n"
            "Você conhece um número de manobras igual a **2 + seu bônus de proficiência** e pode alterar uma manobra "
            "sempre que finalizar um descanso longo. Quando utilizar sua ação de Ataque, você pode usar uma das manobras "
            "marciais às quais tem acesso (incluindo [Ataque Extra](/rules/manobras-marciais#ataque-extra)).\n\n"
            "Consulte a lista completa em [Manobras Marciais](/rules/manobras-marciais)."
        )
        fighter.source_content = fighter.source_content.replace(fighter_extra_attack_old, fighter_maneuvers_new)
        # Note in Two Extra Attacks and Three Extra Attacks
        fighter.source_content = fighter.source_content.replace(
            "### Level 11: Two Extra Attacks\n\n"
            "You can attack three times instead of once whenever you take the Attack action on your turn.",
            "### Level 11: Two Extra Attacks\n\n"
            "You can attack three times instead of once whenever you take the Attack action on your turn. "
            "(Ao utilizar a manobra [Ataque Extra](/rules/manobras-marciais#ataque-extra), você realiza dois ataques adicionais em vez de um)."
        )
        fighter.source_content = fighter.source_content.replace(
            "### Level 20: Three Extra Attacks\n\n"
            "You can attack four times instead of once whenever you take the Attack action on your turn.",
            "### Level 20: Three Extra Attacks\n\n"
            "You can attack four times instead of once whenever you take the Attack action on your turn. "
            "(Ao utilizar a manobra [Ataque Extra](/rules/manobras-marciais#ataque-extra), você realiza três ataques adicionais em vez de um)."
        )
        save_page_with_derived_data(fighter)
        print("   -> Fighter updated.")

        print("4. Updating Class: Barbarian...")
        barbarian = Page.objects.get(slug='barbarian')
        barbarian.source_content = barbarian.source_content.replace(
            "| 5 | +3 | Extra Attack, Fast Movement | 3 | +3 | 3 |",
            "| 5 | +3 | Manobras Marciais (Martial Maneuvers), Fast Movement | 3 | +3 | 3 |"
        )
        barb_extra_attack_old = (
            "### Level 5: Extra Attack\n\n"
            "You can attack twice instead of once whenever you take the Attack action on your turn."
        )
        barb_maneuvers_new = (
            "### Level 5: Manobras Marciais (Martial Maneuvers)\n\n"
            "*Substitui o Extra Attack.* No nível 5 você aprende a realizar [Manobras Marciais](/rules/manobras-marciais). "
            "Seu dado de superioridade inicial é **d4** e aumenta conforme ganha níveis nesta classe (**d6** no nível 6, "
            "**d8** no nível 10, **d10** no nível 14 e **d12** no nível 18).\n\n"
            "Você conhece um número de manobras igual a **2 + seu bônus de proficiência** e pode alterar uma manobra "
            "sempre que finalizar um descanso longo. Quando utilizar sua ação de Ataque, você pode usar uma das manobras "
            "marciais às quais tem acesso (incluindo [Ataque Extra](/rules/manobras-marciais#ataque-extra) e a manobra exclusiva "
            "[Brutalizar](/rules/manobras-marciais#brutalizar)).\n\n"
            "Consulte a lista completa em [Manobras Marciais](/rules/manobras-marciais)."
        )
        barbarian.source_content = barbarian.source_content.replace(barb_extra_attack_old, barb_maneuvers_new)
        save_page_with_derived_data(barbarian)
        print("   -> Barbarian updated.")

        print("5. Updating Class: Monk...")
        monk = Page.objects.get(slug='monk')
        monk.source_content = monk.source_content.replace(
            "| 5 | +3 | Extra Attack, Stunning Strike |",
            "| 5 | +3 | Manobras Marciais (Martial Maneuvers), Stunning Strike |"
        )
        monk_extra_attack_old = (
            "### Level 5: Extra Attack\n\n"
            "You can attack twice instead of once whenever you take the Attack action on your turn."
        )
        monk_maneuvers_new = (
            "### Level 5: Manobras Marciais (Martial Maneuvers)\n\n"
            "*Substitui o Extra Attack.* No nível 5 você aprende a realizar [Manobras Marciais](/rules/manobras-marciais). "
            "Seu dado de superioridade inicial é **d4** e aumenta conforme ganha níveis nesta classe (**d6** no nível 6, "
            "**d8** no nível 10, **d10** no nível 14 e **d12** no nível 18).\n\n"
            "Você conhece um número de manobras igual a **2 + seu bônus de proficiência** e pode alterar uma manobra "
            "sempre que finalizar um descanso longo. Quando utilizar sua ação de Ataque, você pode usar uma das manobras "
            "marciais às quais tem acesso (incluindo [Ataque Extra](/rules/manobras-marciais#ataque-extra) e a manobra exclusiva "
            "[Ataque Atordoante](/rules/manobras-marciais#ataque-atordoante)).\n\n"
            "Consulte a lista completa em [Manobras Marciais](/rules/manobras-marciais)."
        )
        monk.source_content = monk.source_content.replace(monk_extra_attack_old, monk_maneuvers_new)
        save_page_with_derived_data(monk)
        print("   -> Monk updated.")

        print("6. Updating Class: Witcher...")
        witcher = Page.objects.get(slug='witcher')
        witcher.source_content = witcher.source_content.replace(
            "| 5 | 3 | Extra-attack |",
            "| 5 | 3 | Manobras Marciais |"
        )
        witcher_extra_attack_old = (
            "### Nível 5: Ataque extra\n\n"
            "Você pode realizar dois ataques sempre que usar a ação de ataque."
        )
        witcher_maneuvers_new = (
            "### Nível 5: Manobras Marciais\n\n"
            "*Substitui o Extra-Attack.* No nível 5 você aprende a realizar [Manobras Marciais](/rules/manobras-marciais). "
            "Seu dado de superioridade inicial é **d4** e aumenta conforme ganha níveis nesta classe (**d6** no nível 6, "
            "**d8** no nível 10, **d10** no nível 14 e **d12** no nível 18).\n\n"
            "Você conhece um número de manobras igual a **2 + seu bônus de proficiência** e pode alterar uma manobra "
            "sempre que finalizar um descanso longo. Quando utilizar sua ação de Ataque, você pode usar uma das manobras "
            "marciais às quais tem acesso (incluindo [Ataque Extra](/rules/manobras-marciais#ataque-extra) e a manobra exclusiva "
            "[Ataque com Sinal](/rules/manobras-marciais#ataque-com-sinal)).\n\n"
            "Consulte a lista completa em [Manobras Marciais](/rules/manobras-marciais)."
        )
        witcher.source_content = witcher.source_content.replace(witcher_extra_attack_old, witcher_maneuvers_new)
        save_page_with_derived_data(witcher)
        print("   -> Witcher updated.")

        print("7. Updating Class: Herói...")
        heroi = Page.objects.get(slug='heroi')
        heroi.source_content = heroi.source_content.replace(
            "| 5º | 3 | Ataque Extra | 4 | 2 | — | — | — |",
            "| 5º | 3 | Manobras Marciais | 4 | 2 | — | — | — |"
        )
        heroi_extra_attack_old = (
            "### Ataque Extra\n\n"
            "No 5º nível, você pode atacar duas vezes, ao invés de uma, quando usar a ação Atacar durante o seu turno."
        )
        heroi_maneuvers_new = (
            "### Nível 5: Manobras Marciais\n\n"
            "*Substitui o Ataque Extra.* No 5º nível você aprende a realizar [Manobras Marciais](/rules/manobras-marciais). "
            "Como half-marcial, seu dado de superioridade inicial é **d4**, tornando-se **d6** no nível 12 e **d8** no nível 20.\n\n"
            "Você conhece um número de manobras igual ao seu **modificador de conjuração (Carisma), Força ou Destreza (o que for maior)** "
            "e pode alterar uma manobra sempre que finalizar um descanso longo. Quando utilizar sua ação de Ataque, você pode usar uma "
            "das manobras marciais às quais tem acesso (incluindo [Ataque Extra](/rules/manobras-marciais#ataque-extra)).\n\n"
            "Consulte a lista completa em [Manobras Marciais](/rules/manobras-marciais)."
        )
        heroi.source_content = heroi.source_content.replace(heroi_extra_attack_old, heroi_maneuvers_new)
        save_page_with_derived_data(heroi)
        print("   -> Herói updated.")

        print("8. Updating Class: Ranger & Ranger (remake)...")
        ranger = Page.objects.get(slug='ranger')
        ranger.source_content = ranger.source_content.replace(
            "| 5 | +3 | Extra Attack |",
            "| 5 | +3 | Manobras Marciais (Martial Maneuvers) |"
        )
        ranger_extra_attack_old = (
            "### Level 5: Extra Attack\n\n"
            "You can attack twice instead of once whenever you take the Attack action on your turn."
        )
        ranger_maneuvers_new = (
            "### Level 5: Manobras Marciais (Martial Maneuvers)\n\n"
            "*Substitui o Extra Attack.* No nível 5 você aprende a realizar [Manobras Marciais](/rules/manobras-marciais). "
            "Como half-marcial, seu dado de superioridade inicial é **d4**, tornando-se **d6** no nível 12 e **d8** no nível 20.\n\n"
            "Você conhece um número de manobras igual ao seu **modificador de conjuração (Sabedoria), Força ou Destreza (o que for maior)** "
            "e pode alterar uma manobra sempre que finalizar um descanso longo. Quando utilizar sua ação de Ataque, você pode usar uma "
            "das manobras marciais às quais tem acesso (incluindo [Ataque Extra](/rules/manobras-marciais#ataque-extra)).\n\n"
            "Consulte a lista completa em [Manobras Marciais](/rules/manobras-marciais)."
        )
        ranger.source_content = ranger.source_content.replace(ranger_extra_attack_old, ranger_maneuvers_new)
        save_page_with_derived_data(ranger)

        ranger_remake = Page.objects.get(slug='ranger-remake')
        remake_old = (
            "Extra Attack\n\n"
            "Beginning at 5th level, you can attack twice, instead of once, whenever you take the Attack action on your turn."
        )
        remake_new = (
            "### Level 5: Manobras Marciais (Martial Maneuvers)\n\n"
            "*Substitui o Extra Attack.* No nível 5 você aprende a realizar [Manobras Marciais](/rules/manobras-marciais). "
            "Como half-marcial, seu dado de superioridade inicial é **d4**, tornando-se **d6** no nível 12 e **d8** no nível 20.\n\n"
            "Você conhece um número de manobras igual ao seu **modificador de conjuração (Sabedoria), Força ou Destreza (o que for maior)** "
            "e pode alterar uma manobra sempre que finalizar um descanso longo. Quando utilizar sua ação de Ataque, você pode usar uma "
            "das manobras marciais às quais tem acesso (incluindo [Ataque Extra](/rules/manobras-marciais#ataque-extra)).\n\n"
            "Consulte a lista completa em [Manobras Marciais](/rules/manobras-marciais)."
        )
        ranger_remake.source_content = ranger_remake.source_content.replace(remake_old, remake_new)
        save_page_with_derived_data(ranger_remake)
        print("   -> Ranger pages updated.")

        print("9. Updating Class: Paladin...")
        paladin = Page.objects.get(slug='paladin')
        paladin.source_content = paladin.source_content.replace(
            "| 5 | +3 | Extra Attack, Faithful Steed |",
            "| 5 | +3 | Manobras Marciais (Martial Maneuvers), Faithful Steed |"
        )
        paladin_extra_attack_old = (
            "### Level 5: Extra Attack\n\n"
            "You can attack twice instead of once whenever you take the Attack action on your turn."
        )
        paladin_maneuvers_new = (
            "### Level 5: Manobras Marciais (Martial Maneuvers)\n\n"
            "*Substitui o Extra Attack.* No nível 5 você aprende a realizar [Manobras Marciais](/rules/manobras-marciais). "
            "Como half-marcial, seu dado de superioridade inicial é **d4**, tornando-se **d6** no nível 12 e **d8** no nível 20.\n\n"
            "Você conhece um número de manobras igual ao seu **modificador de conjuração (Carisma), Força ou Destreza (o que for maior)** "
            "e pode alterar uma manobra sempre que finalizar um descanso longo. Quando utilizar sua ação de Ataque, você pode usar uma "
            "das manobras marciais às quais tem acesso (incluindo [Ataque Extra](/rules/manobras-marciais#ataque-extra)).\n\n"
            "Consulte a lista completa em [Manobras Marciais](/rules/manobras-marciais)."
        )
        paladin.source_content = paladin.source_content.replace(paladin_extra_attack_old, paladin_maneuvers_new)
        save_page_with_derived_data(paladin)
        print("   -> Paladin updated.")

        print("10. Updating Class: Filho da Magia (Magic Born)...")
        filho = Page.objects.get(slug='filho-da-magia')
        filho.source_content = filho.source_content.replace(
            "| 5º | 3 | Ataque Extra | 5 | 4 | 2 | — | — | — |",
            "| 5º | 3 | Manobras Marciais | 5 | 4 | 2 | — | — | — |"
        )
        filho_extra_attack_old = (
            "### Nível 5: Ataque Extra\n\n"
            "Você pode atacar duas vezes, em vez de uma, sempre que usar a ação Atacar no seu turno."
        )
        filho_maneuvers_new = (
            "### Nível 5: Manobras Marciais\n\n"
            "*Substitui o Ataque Extra.* No 5º nível você aprende a realizar [Manobras Marciais](/rules/manobras-marciais). "
            "Como half-marcial, seu dado de superioridade inicial é **d4**, tornando-se **d6** no nível 12 e **d8** no nível 20.\n\n"
            "Você conhece um número de manobras igual ao seu **modificador de conjuração (Carisma), Força ou Destreza (o que for maior)** "
            "e pode alterar uma manobra sempre que finalizar um descanso longo. Quando utilizar sua ação de Ataque, você pode usar uma "
            "das manobras marciais às quais tem acesso (incluindo [Ataque Extra](/rules/manobras-marciais#ataque-extra)).\n\n"
            "Consulte a lista completa em [Manobras Marciais](/rules/manobras-marciais)."
        )
        filho.source_content = filho.source_content.replace(filho_extra_attack_old, filho_maneuvers_new)
        save_page_with_derived_data(filho)
        print("   -> Filho da Magia updated.")

        print("11. Updating Class: Cavaleiro da Morte...")
        cdm = Page.objects.get(slug='cavaleiro-da-morte')
        cdm.source_content = cdm.source_content.replace(
            "| 5 | +3 | Ataque Extra | 4 | 2º | 4 | +3d8 |",
            "| 5 | +3 | Manobras Marciais | 4 | 2º | 4 | +3d8 |"
        ).replace(
            "| 5 | +3 | Ataque Extra | 4 | 2\ufffd | 4 | +3d8 |",
            "| 5 | +3 | Manobras Marciais | 4 | 2\ufffd | 4 | +3d8 |"
        )
        cdm_maneuvers_new = (
            "### Nível 5: Manobras Marciais\n\n"
            "*Substitui o Ataque Extra.* No 5º nível você aprende a realizar [Manobras Marciais](/rules/manobras-marciais). "
            "Como half-marcial, seu dado de superioridade inicial é **d4**, tornando-se **d6** no nível 12 e **d8** no nível 20.\n\n"
            "Você conhece um número de manobras igual ao seu **modificador de conjuração (Carisma), Força ou Destreza (o que for maior)** "
            "e pode alterar uma manobra sempre que finalizar um descanso longo. Quando utilizar sua ação de Ataque, você pode usar uma "
            "das manobras marciais às quais tem acesso (incluindo [Ataque Extra](/rules/manobras-marciais#ataque-extra) e a manobra exclusiva "
            "[Ataque da Morte](/rules/manobras-marciais#ataque-da-morte)).\n\n"
            "Consulte a lista completa em [Manobras Marciais](/rules/manobras-marciais).\n\n"
        )
        cdm.source_content = re.sub(
            r'### Ataque Extra\s*\n+A partir do 5[^\n]*\n+',
            cdm_maneuvers_new,
            cdm.source_content
        )
        save_page_with_derived_data(cdm)
        print("   -> Cavaleiro da Morte updated.")

        print("12. Updating Class: Caçador de Demônios (Demon Hunter)...")
        cdd = Page.objects.get(slug='cacador-de-demonios')
        cdd.source_content = cdd.source_content.replace(
            "| 5 | +3 | Ataque Extra | +3 m | 4 | 4 | 2 | — | — | — |",
            "| 5 | +3 | Manobras Marciais | +3 m | 4 | 4 | 2 | — | — | — |"
        ).replace(
            "| 5 | +3 | Ataque Extra | +3 m | 4 | 4 | 2 | \ufffd | \ufffd | \ufffd |",
            "| 5 | +3 | Manobras Marciais | +3 m | 4 | 4 | 2 | \ufffd | \ufffd | \ufffd |"
        )
        cdd_maneuvers_new = (
            "### Nível 5: Manobras Marciais\n\n"
            "*Substitui o Ataque Extra.* No 5º nível você aprende a realizar [Manobras Marciais](/rules/manobras-marciais). "
            "Como half-marcial, seu dado de superioridade inicial é **d4**, tornando-se **d6** no nível 12 e **d8** no nível 20.\n\n"
            "Você conhece um número de manobras igual ao seu **modificador de conjuração (Carisma), Força ou Destreza (o que for maior)** "
            "e pode alterar uma manobra sempre que finalizar um descanso longo. Quando utilizar sua ação de Ataque, você pode usar uma "
            "das manobras marciais às quais tem acesso (incluindo [Ataque Extra](/rules/manobras-marciais#ataque-extra)).\n\n"
            "Consulte a lista completa em [Manobras Marciais](/rules/manobras-marciais).\n\n"
        )
        cdd.source_content = re.sub(
            r'### Ataque Extra\s*\n+A partir do 5[^\n]*\n+',
            cdd_maneuvers_new,
            cdd.source_content
        )
        save_page_with_derived_data(cdd)
        print("   -> Caçador de Demônios updated.")

        print("13. Updating Class: Dovahkiin...")
        dov = Page.objects.get(slug='dovahkiin')
        dov.source_content = dov.source_content.replace(
            "| 5 | 3 | Extra-attack | 4 | 2 |  |  |  |",
            "| 5 | 3 | Manobras Marciais | 4 | 2 |  |  |  |"
        )
        dov_extra_attack_old = "### Nível 5: ataque extra"
        dov_maneuvers_new = (
            "### Nível 5: Manobras Marciais\n\n"
            "*Substitui o Ataque Extra.* No 5º nível você aprende a realizar [Manobras Marciais](/rules/manobras-marciais). "
            "Como half-marcial, seu dado de superioridade inicial é **d4**, tornando-se **d6** no nível 12 e **d8** no nível 20.\n\n"
            "Você conhece um número de manobras igual ao seu **modificador de conjuração (Carisma), Força ou Destreza (o que for maior)** "
            "e pode alterar uma manobra sempre que finalizar um descanso longo. Quando utilizar sua ação de Ataque, você pode usar uma "
            "das manobras marciais às quais tem acesso (incluindo [Ataque Extra](/rules/manobras-marciais#ataque-extra)).\n\n"
            "Consulte a lista completa em [Manobras Marciais](/rules/manobras-marciais)."
        )
        dov.source_content = dov.source_content.replace(dov_extra_attack_old, dov_maneuvers_new)
        save_page_with_derived_data(dov)
        print("   -> Dovahkiin updated.")

        print("14. Updating Artificer Subclasses (Battle Smith, Armorer, Cosmic Tinker)...")
        # Battle Smith
        bs = Page.objects.get(slug='battle-smith')
        bs_old = (
            "### Level 5: Extra Attack\n\n"
            "You can attack twice instead of once whenever you take the Attack action on your turn. "
            "You can forgo one of your attacks when you take the Attack action to command your Steel Defender to take the Force-Empowered Rend action."
        )
        bs_new = (
            "### Level 5: Manobras Marciais (Martial Maneuvers)\n\n"
            "*Substitui o Extra Attack.* No nível 5 você aprende a realizar [Manobras Marciais](/rules/manobras-marciais). "
            "Seu dado de superioridade inicial é **d4**. No nível 12 seu dado de superioridade se torna **d6** e no nível 20 se torna **d8**.\n\n"
            "Você conhece um número de manobras igual ao seu modificador de **Inteligência** e pode alterar uma manobra sempre que ganhar "
            "um novo nível nesta classe. Quando utilizar sua ação de Ataque, você pode usar uma das manobras marciais às quais tem acesso. "
            "Se escolher usar a manobra [Ataque Extra](/rules/manobras-marciais#ataque-extra), você pode renunciar a um de seus ataques para "
            "comandar seu Defensor de Aço (*Steel Defender*) a realizar a ação Force-Empowered Rend.\n\n"
            "**Manobras Disponíveis:**\n"
            "- [Isca e Troca](/rules/manobras-marciais#isca-e-troca)\n"
            "- [Apostar](/rules/manobras-marciais#apostar)\n"
            "- [Ataque Distrativo](/rules/manobras-marciais#ataque-distrativo)\n"
            "- [Ataque Extra](/rules/manobras-marciais#ataque-extra)\n"
            "- [Ataque de Manobra](/rules/manobras-marciais#ataque-de-manobra)\n"
            "- [Expelir Magia](/rules/manobras-marciais#expelir-magia)\n"
            "- [Ataque em Avanço](/rules/manobras-marciais#ataque-em-avanco) *(Apenas Battle Smith)*\n"
            "- [Cortar Tendões](/rules/manobras-marciais#cortar-tendoes)\n"
            "- [Ataque de Confusão](/rules/manobras-marciais#ataque-de-confusao)"
        )
        bs.source_content = bs.source_content.replace(bs_old, bs_new)
        save_page_with_derived_data(bs)

        # Armorer
        armorer = Page.objects.get(slug='armorer')
        arm_old = (
            "### Level 5: Extra Attack\n\n"
            "You can attack twice instead of once whenever you take the Attack action on your turn."
        )
        arm_new = (
            "### Level 5: Manobras Marciais (Martial Maneuvers)\n\n"
            "*Substitui o Extra Attack.* No nível 5 você aprende a realizar [Manobras Marciais](/rules/manobras-marciais). "
            "Seu dado de superioridade inicial é **d4**. No nível 12 seu dado de superioridade se torna **d6** e no nível 20 se torna **d8**.\n\n"
            "Você conhece um número de manobras igual ao seu modificador de **Inteligência** e pode alterar uma manobra sempre que ganhar "
            "um novo nível nesta classe. Quando utilizar sua ação de Ataque, você pode usar uma das manobras marciais às quais tem acesso.\n\n"
            "**Manobras Disponíveis:**\n"
            "- [Isca e Troca](/rules/manobras-marciais#isca-e-troca)\n"
            "- [Apostar](/rules/manobras-marciais#apostar)\n"
            "- [Ataque Distrativo](/rules/manobras-marciais#ataque-distrativo)\n"
            "- [Ataque Extra](/rules/manobras-marciais#ataque-extra)\n"
            "- [Ataque de Manobra](/rules/manobras-marciais#ataque-de-manobra)\n"
            "- [Expelir Magia](/rules/manobras-marciais#expelir-magia)\n"
            "- [Cortar Tendões](/rules/manobras-marciais#cortar-tendoes)\n"
            "- [Ataque de Confusão](/rules/manobras-marciais#ataque-de-confusao)"
        )
        armorer.source_content = armorer.source_content.replace(arm_old, arm_new)
        save_page_with_derived_data(armorer)

        # Cosmic Tinker
        ct = Page.objects.get(slug='cosmic-tinker-artificer')
        ct_old = (
            "### Nível 5: Extra Attack\n\n"
            "Starting at 5th level, you can attack twice, instead of once, whenever you take the Attack action on your turn."
        )
        ct_new = (
            "### Nível 5: Manobras Marciais (Martial Maneuvers)\n\n"
            "*Substitui o Extra Attack.* No nível 5 você aprende a realizar [Manobras Marciais](/rules/manobras-marciais). "
            "Seu dado de superioridade inicial é **d4**. No nível 12 seu dado de superioridade se torna **d6** e no nível 20 se torna **d8**.\n\n"
            "Você conhece um número de manobras igual ao seu modificador de **Inteligência** e pode alterar uma manobra sempre que ganhar "
            "um novo nível nesta classe. Quando utilizar sua ação de Ataque, você pode usar uma das manobras marciais às quais tem acesso.\n\n"
            "**Manobras Disponíveis:**\n"
            "- [Isca e Troca](/rules/manobras-marciais#isca-e-troca)\n"
            "- [Apostar](/rules/manobras-marciais#apostar)\n"
            "- [Ataque Distrativo](/rules/manobras-marciais#ataque-distrativo)\n"
            "- [Ataque Extra](/rules/manobras-marciais#ataque-extra)\n"
            "- [Ataque de Manobra](/rules/manobras-marciais#ataque-de-manobra)\n"
            "- [Expelir Magia](/rules/manobras-marciais#expelir-magia)\n"
            "- [Cortar Tendões](/rules/manobras-marciais#cortar-tendoes)\n"
            "- [Ataque de Confusão](/rules/manobras-marciais#ataque-de-confusao)"
        )
        ct.source_content = ct.source_content.replace(ct_old, ct_new)
        save_page_with_derived_data(ct)
        print("   -> Artificer subclasses updated.")

        print("15. Updating Bard Subclass: College of Valor...")
        valor = Page.objects.get(slug='college-of-valor')
        valor_old = (
            "### Level 6: Extra Attack\n\n"
            "You can attack twice instead of once whenever you take the Attack action on your turn.\n\n"
            "In addition, you can cast one of your cantrips that has a casting time of an action in place of one of those attacks."
        )
        valor_new = (
            "### Level 6: Manobras Marciais (Martial Maneuvers)\n\n"
            "*Substitui o Extra Attack.* No nível 6 você aprende a realizar [Manobras Marciais](/rules/manobras-marciais). "
            "Seu dado de superioridade inicial é **d4** e no nível 18 se torna **d6**.\n\n"
            "Você conhece um número de manobras igual ao seu modificador de **Carisma** e pode alterar uma manobra sempre que ganhar "
            "um novo nível nesta classe. Quando utilizar sua ação de Ataque, você pode usar uma das manobras marciais às quais tem acesso.\n\n"
            "**Manobras Disponíveis:**\n"
            "- [Emboscada](/rules/manobras-marciais#emboscada)\n"
            "- [Isca e Troca](/rules/manobras-marciais#isca-e-troca)\n"
            "- [Apostar](/rules/manobras-marciais#apostar)\n"
            "- [Ataque Distrativo](/rules/manobras-marciais#ataque-distrativo)\n"
            "- [Ataque Extra](/rules/manobras-marciais#ataque-extra) *(você pode substituir um ataque por um truque/cantrip que tenha tempo de conjuração de 1 ação)*\n"
            "- [Ataque Desarmante](/rules/manobras-marciais#ataque-desarmante)\n"
            "- [Expelir Magia](/rules/manobras-marciais#expelir-magia)\n"
            "- [Ataque em Avanço](/rules/manobras-marciais#ataque-em-avanco)\n"
            "- [Ataque Desnorteante](/rules/manobras-marciais#ataque-desnorteante)"
        )
        valor.source_content = valor.source_content.replace(valor_old, valor_new)
        save_page_with_derived_data(valor)
        print("   -> College of Valor updated.")

        print("16. Updating Wizard Subclass: Bladesinger...")
        bsinger = Page.objects.get(slug='bladesinger')
        bsinger_old = (
            "### Level 6: Extra Attack\n\n"
            "You can attack twice, instead of once, whenever you take the Attack action on your turn. "
            "Moreover, you can cast one of your Wizard cantrips that has a casting time of an action in place of one of those attacks."
        )
        bsinger_new = (
            "### Level 6: Manobras Marciais (Martial Maneuvers)\n\n"
            "*Substitui o Extra Attack.* No nível 6 você aprende a realizar [Manobras Marciais](/rules/manobras-marciais). "
            "Seu dado de superioridade inicial é **d4** e no nível 18 se torna **d6**.\n\n"
            "Você conhece um número de manobras igual ao seu modificador de **Inteligência** e pode alterar uma manobra sempre que ganhar "
            "um novo nível nesta classe. Quando utilizar sua ação de Ataque, você pode usar uma das manobras marciais às quais tem acesso.\n\n"
            "**Manobras Disponíveis:**\n"
            "- [Emboscada](/rules/manobras-marciais#emboscada)\n"
            "- [Ataque Desarmante](/rules/manobras-marciais#ataque-desarmante)\n"
            "- [Ataque Extra](/rules/manobras-marciais#ataque-extra) *(você pode substituir um ataque por um truque de Mago com tempo de conjuração de 1 ação)*\n"
            "- [Ataque de Manobra](/rules/manobras-marciais#ataque-de-manobra)\n"
            "- [Ataque em Avanço](/rules/manobras-marciais#ataque-em-avanco)\n"
            "- [Ataque Rasteira](/rules/manobras-marciais#ataque-rasteira)\n"
            "- [Expelir Magia](/rules/manobras-marciais#expelir-magia)"
        )
        bsinger.source_content = bsinger.source_content.replace(bsinger_old, bsinger_new)
        save_page_with_derived_data(bsinger)
        print("   -> Bladesinger updated.")

        print("17. Updating Warlock Invocations (Thirsting Blade & Devouring Blade)...")
        ei = Page.objects.get(slug='eldritch-invocation')
        thirsting_old = (
            "### Thirsting Blade\n\n"
            "You gain the Extra Attack feature for your pact weapon only. "
            "With that feature, you can attack twice with the weapon instead of once when you take the Attack action on your turn."
        )
        thirsting_new = (
            "### Thirsting Blade\n\n"
            "*Pré-requisito: Nível 5+, Pact of the Blade.*\n\n"
            "Você aprende a realizar [Manobras Marciais](/rules/manobras-marciais) exclusivamente com sua arma do pacto. "
            "Seu dado de superioridade inicial é **d4** e no nível 18 se torna **d6**.\n\n"
            "Você conhece um número de manobras igual ao seu modificador de **Carisma** e pode alterar uma manobra sempre que ganhar "
            "um novo nível nesta classe. Quando utilizar sua ação de Ataque com sua arma do pacto, você pode usar uma das manobras às quais "
            "tem acesso. Se utilizar a manobra [Ataque Extra](/rules/manobras-marciais#ataque-extra), você pode substituir um dos ataques por "
            "um truque (*cantrip*) com tempo de conjuração de 1 ação.\n\n"
            "**Manobras Disponíveis:**\n"
            "- [Emboscada](/rules/manobras-marciais#emboscada)\n"
            "- [Ataque Agarrador](/rules/manobras-marciais#ataque-agarrador)\n"
            "- [Ataque Distrativo](/rules/manobras-marciais#ataque-distrativo)\n"
            "- [Ataque Extra](/rules/manobras-marciais#ataque-extra) *(pode substituir 1 ataque por truque)*\n"
            "- [Ataque Desarmante](/rules/manobras-marciais#ataque-desarmante)\n"
            "- [Arremesso Rápido](/rules/manobras-marciais#arremesso-rapido)\n"
            "- [Expelir Magia](/rules/manobras-marciais#expelir-magia)\n"
            "- [Ataque em Avanço](/rules/manobras-marciais#ataque-em-avanco)\n"
            "- [Ataque Varredura](/rules/manobras-marciais#ataque-varredura)\n"
            "- [Ataque Desnorteante](/rules/manobras-marciais#ataque-desnorteante)\n"
            "- [Abate](/rules/manobras-marciais#abate)\n"
            "- [Cortar Tendões](/rules/manobras-marciais#cortar-tendoes)\n"
            "- [Onda de Choque](/rules/manobras-marciais#onda-de-choque)"
        )
        ei.source_content = ei.source_content.replace(thirsting_old, thirsting_new)
        ei.source_content = ei.source_content.replace(
            "### Devouring Blade\n\n"
            "The Extra Attack of your Thirsting Blade invocation confers two extra attacks rather than one.",
            "### Devouring Blade\n\n"
            "Ao utilizar a manobra [Ataque Extra](/rules/manobras-marciais#ataque-extra) concedida pela invocação Thirsting Blade, "
            "ela concede dois ataques adicionais em vez de um (total de três ataques)."
        )
        save_page_with_derived_data(ei)
        print("   -> Eldritch Invocations updated.")

        print("18. Updating Xamã & Druid Subclasses...")
        xama = Page.objects.get(slug='xama-caminho-do-aperfeicoamento')
        xama_maneuvers_new = (
            "#### Manobras Marciais (6º nível)\n\n"
            "*Substitui o Ataque Extra.* A partir do 6º nível, você ganha acesso a [Manobras Marciais](/rules/manobras-marciais) "
            "com dado de superioridade inicial **d4** (tornando-se **d6** no nível 18). Você conhece um número de manobras igual ao seu "
            "modificador de Sabedoria e pode usar uma manobra (incluindo [Ataque Extra](/rules/manobras-marciais#ataque-extra)) ao realizar a ação de Ataque.\n\n"
        )
        xama.source_content = re.sub(
            r'#### Ataque Extra \(6[^\n]*\n+A partir do 6[^\n]*\n+',
            xama_maneuvers_new,
            xama.source_content
        )
        save_page_with_derived_data(xama)

        druid_sub = Page.objects.get(slug='circulo-da-ordenacao-dos-mundos-druida')
        druid_sub.source_content = druid_sub.source_content.replace(
            "| Extra-attack. A partir do nível 5, você pode realizar dois ataques quando usar a ação de Ataque |",
            "| Manobras Marciais (ou Ataque Extra). A partir do nível 5, você acessa [Manobras Marciais](/rules/manobras-marciais) (dado d4) |"
        )
        save_page_with_derived_data(druid_sub)
        print("   -> Xamã and Druid subclass updated.")

        print("19. Updating Spells: Haste & Tenser's Transformation...")
        haste = Page.objects.get(slug='haste')
        haste.source_content = haste.source_content.replace(
            "That action can be used to take only the Attack (one attack only), Dash, Disengage, Hide, or Utilize action.",
            "That action can be used to take only the Attack (one attack only; **não pode usar manobras nesse ataque**), Dash, Disengage, Hide, or Utilize action."
        )
        save_page_with_derived_data(haste)

        tenser = Page.objects.get(slug='tensers-transformation')
        tenser_attack_old = "- You can attack twice, instead of once, when you take the Attack action on your turn. You ignore this benefit if you already have a feature, like Extra Attack, that gives you extra attacks."
        tenser_attack_new = (
            "- Você recebe a capacidade de usar as seguintes [Manobras Marciais](/rules/manobras-marciais) com um dado de superioridade **d4**: "
            "[Ataque Extra](/rules/manobras-marciais#ataque-extra), "
            "[Ataque de Empurrão](/rules/manobras-marciais#ataque-de-empurrao), "
            "[Expelir Magia](/rules/manobras-marciais#expelir-magia), "
            "[Ataque Varredura](/rules/manobras-marciais#ataque-varredura)."
        )
        tenser.source_content = tenser.source_content.replace(tenser_attack_old, tenser_attack_new)
        save_page_with_derived_data(tenser)
        print("   -> Haste and Tenser's Transformation updated.")

        print("20. Creating / Updating Spell: Tasha's Otherworldly Guise...")
        tasha_content = (
            "*6th-level transmutation*\n\n"
            "**Casting Time:** 1 bonus action\n\n"
            "**Range:** Self\n\n"
            "**Components:** V, S, M (an object engraved with a symbol of the Outer Planes worth at least 500 gp)\n\n"
            "**Duration:** Concentration, up to 1 minute\n\n"
            "Ao proferir um encantamento, você canaliza a magia dos Planos Inferiores ou dos Planos Superiores (à sua escolha) para se transformar. Você recebe os seguintes benefícios até a magia terminar:\n\n"
            "- Você é imune a dano de fogo e de veneno (Planos Inferiores) ou a dano radiante e necrótico (Planos Superiores).\n"
            "- Você é imune à condição envenenado (Planos Inferiores) ou à condição enfeitiçado (Planos Superiores).\n"
            "- Asas espectrais surgem nas suas costas, concedendo a você um deslocamento de voo de 12 metros (40 pés).\n"
            "- Você recebe um bônus de +2 na Classe de Armadura (CA).\n"
            "- Todos os seus ataques com arma são mágicos e, ao realizar um ataque com arma, você pode usar o modificador da sua habilidade de conjuração em vez de Força ou Destreza para as jogadas de ataque e de dano.\n"
            "- Você recebe a capacidade de usar as seguintes [Manobras Marciais](/rules/manobras-marciais) com um dado de superioridade **d4**:\n"
            "  - [Ataque Extra](/rules/manobras-marciais#ataque-extra)\n"
            "  - [Ataque Desarmante](/rules/manobras-marciais#ataque-desarmante)\n"
            "  - [Expelir Magia](/rules/manobras-marciais#expelir-magia)\n"
            "  - [Ataque em Avanço](/rules/manobras-marciais#ataque-em-avanco)\n\n"
            "***Spell Lists.*** [Sorcerer](/classes/sorcerer), [Warlock](/classes/warlock), [Wizard](/classes/wizard)\n"
        )
        tasha_page, t_created = Page.objects.get_or_create(
            slug='tashas-otherworldly-guise',
            defaults={
                'title': "Tasha's Otherworldly Guise",
                'category': spells_cat,
                'source': 'homebrew',
                'visibility': 'public',
                'structured_data': {
                    'level': 6,
                    'school': 'Transmutation',
                    'range': 'Self',
                    'duration': 'Concentration, up to 1 minute',
                    'components': 'V, S, M (an object engraved with a symbol of the Outer Planes worth at least 500 gp)',
                    'casting_time': '1 bonus action',
                    'classes': ['sorcerer', 'warlock', 'wizard']
                },
                'source_content': tasha_content
            }
        )
        if not t_created:
            tasha_page.source_content = tasha_content
            tasha_page.structured_data = {
                'level': 6,
                'school': 'Transmutation',
                'range': 'Self',
                'duration': 'Concentration, up to 1 minute',
                'components': 'V, S, M (an object engraved with a symbol of the Outer Planes worth at least 500 gp)',
                'casting_time': '1 bonus action',
                'classes': ['sorcerer', 'warlock', 'wizard']
            }
        save_page_with_derived_data(tasha_page, tag_names=['magia', 'transmutação', 'nível-6', 'manobras'])
        print(f"   -> Spell 'tashas-otherworldly-guise' saved successfully (created={t_created}).")

    print("\nALL UPDATES COMPLETED SUCCESSFULLY!")

if __name__ == '__main__':
    apply_all()
