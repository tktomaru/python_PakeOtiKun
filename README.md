# パケ落ちくんとは？

パケ落ちくんはネットワークエミュレーターです。
Lanの途中に挟むことで、ネットワークに対し以下のことができます。

- 遅延(DELAY)
- 廃棄(LOSS)
- 破壊(CORRUPT) : PakeOtiKun4とPakeOtiKunRSが対応
- 重複(DUPLICATION) : PakeOtiKun4とPakeOtiKunRSが対応
- 並び替え(REORDERING) : PakeOtiKunRSが対応

# ブログ


# パケ落ちくんソースコード

- PakeOtiKun.py : DSAS様の作成されたものと同じものをpythonにしました
- PakeOtiKun4.py : PakeOtiKunにおいて可変抵抗が2つだったものを4つにしたものです
- PakeOtiKunRS.py : 可変抵抗は4つでロータリースイッチを追加したものです

