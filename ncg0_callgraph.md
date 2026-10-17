# ncg0 (Core.dll) - call graph & function structure

Static, from the deobfuscated stream. Direct `call rel32` edges only;
indirect/virtual calls (C++ vtables) are not edges, so true fan-out is higher.

## Totals
- functions: **2879**
- direct call edges: **3007** (distinct callees 2653)
- leaf functions: **2082**   root/uncalled (entry/export candidates): **226**

## Most-called functions (runtime/utility hubs)
| addr | calls in | out-deg | role |
|---|---|---|---|
| sub_042c14 | 28 | 1 |  |
| sub_0affa7 | 28 | 1 | get-EIP (PIC) thunk |
| sub_00f2a7 | 25 | 5 |  |
| sub_040506 | 23 | 0 | memset (byte-fill loop) |
| sub_02303e | 21 | 2 |  |
| sub_01bb4a | 20 | 1 |  |
| sub_03e8e0 | 19 | 5 |  |
| sub_01913b | 17 | 1 |  |
| sub_041b1b | 16 | 2 |  |
| sub_045b6e | 16 | 1 |  |
| sub_0b02ef | 16 | 1 |  |
| sub_03feda | 15 | 2 |  |
| sub_0408fc | 15 | 2 |  |
| sub_0b04e0 | 12 | 1 |  |
| sub_0aeb91 | 11 | 10 |  |
| sub_0195bd | 10 | 1 |  |
| sub_03f276 | 10 | 3 |  |
| sub_0443db | 9 | 4 |  |
| sub_02465e | 8 | 6 |  |
| sub_050968 | 8 | 1 |  |

## Highest out-degree (orchestrators / init)
| addr | out-deg | calls in |
|---|---|---|
| sub_03217a | 40 | 1 |
| sub_00fbc3 | 24 | 2 |
| sub_028de5 | 21 | 0 |
| sub_01af36 | 20 | 1 |
| sub_031008 | 18 | 1 |
| sub_05421d | 18 | 1 |
| sub_0271d3 | 17 | 1 |
| sub_01a3d0 | 16 | 1 |
| sub_080afc | 16 | 1 |
| sub_019a55 | 15 | 1 |
| sub_026552 | 15 | 1 |
| sub_039183 | 15 | 1 |
| sub_08146e | 15 | 0 |
| sub_0a895e | 15 | 0 |
| sub_0ac4af | 15 | 1 |
| sub_02d93f | 14 | 0 |
| sub_0576fa | 14 | 1 |
| sub_05fd9d | 14 | 0 |
| sub_061d38 | 14 | 1 |
| sub_077a72 | 14 | 0 |
