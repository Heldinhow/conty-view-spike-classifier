# Conty. view-spike-classifier

Classifica uma série de views por hora como `legitimate`, `suspicious` ou `inconclusive`. A regra central é explicável: pico alto combinado com queda abrupta ou platô mecânico indica pico comprado; pico intermediário com decaimento médio cai na zona cinzenta, que prefere não acusar. A série tem entre 24 e 168 pontos horários.

## Regras principais

- Pico de 5x ou mais sobre a mediana com queda abrupta (`drop_ratio<=0.4`) ou platô mecânico (`flat_score>=0.4`) é `suspicious`; o motivo cita nominalmente os sinais que decidiram.
- Pico entre 3x e 5x sobre a mediana é `inconclusive`: zona cinzenta que prefere não acusar e nunca conta como falso positivo.
- Série com mediana zerada ou pico na borda temporal (sem baseline ou sem pós-pico para medir a queda) é `inconclusive`, nunca `suspicious`.
- Sem nenhum ponto acima da mediana (série constante, pico 1.0x) é `legitimate`.
- Série válida tem de 24 a 168 pontos, só números não-negativos; fora disso a API devolve 422.
- Rota desconhecida devolve 404 com precedência sobre 422 (`404 > 422`).
- Taxa de falso positivo medida sobre o dataset sintético: `EXPECTED_FP=0.0000` (0/100 legítimas marcadas como suspeitas; inconclusivas sobre legítimas: 0.0300, só reportada).

## Como rodar

Python 3, só standard library, sem dependências para instalar.

```bash
python3 scripts/eval.py --seed 42
python3 -m unittest
python3 server.py
```

`scripts/eval.py` gera `data/dataset.json` com a seed fixa (padrão 42, `--seed` troca) e mede a taxa de falso positivo, imprimindo e persistindo o resultado. A API sobe em `http://127.0.0.1:8000`.

```bash
curl -s -X POST localhost:8000/classify \
  -H 'content-type: application/json' \
  -d '{"views":[100,102,98,101,99,103,100,97,100,102,98,101,99,103,100,97,100,102,98,101,99,103,100,97]}'
```

Os testes descrevem o comportamento esperado.

## Contrato da API

`POST /classify` recebe `{"views":[...]}` e devolve `{"verdict","reason","signals"}`:

| Caso | Status | Corpo |
|---|---|---|
| Série válida (24–168 pontos, só números não-negativos) | 200 | `{"verdict":"legitimate"\|"suspicious"\|"inconclusive","reason":"...","signals":{"spike_ratio":n,"drop_ratio":n,"flat_score":n}}` |
| Série inválida (vazia, fora da janela 24–168, negativa ou não-numérica) | 422 | `{"error":"invalid series"}` |
| Rota desconhecida (qualquer método) | 404 | `{"error":"not found"}` |

Precedência de erro: `404 > 422` — rota desconhecida devolve 404 mesmo com corpo inválido. `reason` é texto legível que cita os sinais; `spike_ratio=null` (mediana zerada, sem baseline) só ocorre em veredito `inconclusive`.

## Exemplos

Sucesso, base estável:

```bash
curl -s -X POST localhost:8000/classify \
  -H 'content-type: application/json' \
  -d '{"views":[100,102,98,101,99,103,100,97,100,102,98,101,99,103,100,97,100,102,98,101,99,103,100,97]}'
```

```json
{"verdict": "legitimate", "reason": "base estável: pico de apenas 1.03x sobre a mediana (spike_ratio=1.03), sem queda abrupta (drop_ratio=0.961) nem repetição mecânica (flat_score=0.0).", "signals": {"spike_ratio": 1.03, "drop_ratio": 0.961, "flat_score": 0.0}}
```

Sucesso, platô mecânico:

```bash
curl -s -X POST localhost:8000/classify \
  -H 'content-type: application/json' \
  -d '{"views":[100,102,98,600,600,600,55,50,100,102,98,600,600,600,55,50,100,102,98,600,600,600,55,50]}'
```

```json
{"verdict": "suspicious", "reason": "pico comprado: pico de 5.941x sobre a mediana (spike_ratio=5.941) com platô mecânico (flat_score=0.4, drop_ratio=0.697).", "signals": {"spike_ratio": 5.941, "drop_ratio": 0.697, "flat_score": 0.4}}
```

Série inválida:

```bash
curl -s -X POST localhost:8000/classify \
  -H 'content-type: application/json' \
  -d '{"views":[]}'
```

```json
{"error": "invalid series"}
```

Rota desconhecida (precedência sobre corpo inválido):

```bash
curl -s -X POST localhost:8000/nope \
  -H 'content-type: application/json' \
  -d '{"views":[]}'
```

```json
{"error": "not found"}
```

## Fora de escopo

- Enchimento gradual sem pico e bot diluído NÃO são detectados: sem pico alto a série cai em `legitimate` ou na zona `inconclusive`, nunca em `suspicious`.
- Sem banco de dados, autenticação, rede social real, UI, concorrência ou tuning de performance.

## Uso de IA

### Feito com IA

Núcleo classificador, dataset sintético, adaptador HTTP e testes gerados por implementadores IA com TDD.

### Revisado por humano

Verificado à mão com os comandos literais:

```bash
python3 scripts/eval.py
python3 -m unittest
```

O contrato é este README e os testes.
