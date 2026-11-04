# Glossary - Paro Wars

Binding for every translator and reviewer. Agents propose additions in reports; only the controller edits this file.
`tools/batches.py check` enforces the tables on story, ending, unit and battle text (JP forms split by ` / `, EN forms likewise).

## Rulings (asked of the user once; options and reasons in docs/decisions.md)
- Honorifics: kept, hyphenated. Name order: Western (given name first).
- Romanisation source: official Konami English names where they exist, else Hepburn without macrons (no earlier patch exists).
- Credits: English.
- Register / flavour: comedy war parody; keep the jokes and punny unit names punchy, even if the literal meaning shifts. Sound effects: plain English words with stretched letters and !! ("Yeeow!!"), never romaji where an English shout exists.
- Abbreviations: full names and terms everywhere, prefer engine changes over shortening. Flagged exceptions: the 12 px one-kanji table headers (terrain, weapon flags) get two letters, listed below, because the columns are one kanji wide.

## Style rules
- Punctuation map: 「」 -> "...", 『』 -> '...', ・・・ -> ..., ！？ -> !?, ！！ -> !!, ～ at a line's end stretches the word or becomes !, never kept as ~ except in Moai/Takosuke-style quirk tails (see style reference).
- Speaker labels: `Nyanjiro: "line"`. Layout spaces inside a page are dropped; the tool breaks lines. Greek stays verbatim.
- Voices: `docs/style-reference.md`.

## Characters
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| ペン太郎 / ペンタロウ | Pentaro | | penguin king; Parodius' Pentarou. `ペンタロウキング３世` = King Pentaro III | Pentarou |
| ニャン次郎 | Nyanjiro | | full name John Nyanjiro, peddler cat | Nyanjirou |
| ニャー・ムー | Nya-Mu | | Nyanjiro's true self, Emperor of the Nya Continent; LATE REVEAL, chapter 6 | |
| アンナパブロワ | Anna Pavlova | | panda leader, speaks with -aru | Anna Paburowa |
| よしこ女帝 | Empress Yoshiko | | moai leader, speaks with -mo | |
| ミカエル | Michael | | pig emperor, Parodius' Michael | Mikael |
| タコスケ | Takosuke | | octopus Fuehrer, `Ａ．タコスケＪｒ．` = A. Takosuke Jr. | Tako |
| テンペ | Tenpe | | feng-shui guru, Nyanjiro's friend | |
| ポチ之嵐 / ポチの嵐 | Pochi-no-Arashi | | dog prime minister | |
| ペン花子 | Pen-Hanako | | | |

Hiragana names (not enforced because the same letters are pronouns): こいつ Koitsu, あいつ Aitsu, ひかる Hikaru, あかね Akane, こいつ書記長 General Secretary Koitsu, あいつ大統領 President Aitsu. Koitsu speaks only Greek letters.

## Places
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| ペン太郎王国 / ペンタロウ王国 / ペンタ王国 | Pentaro Kingdom / Penta Kingdom | | | |
| ミカエル帝国 | Michael Empire | | | |
| アカシヤランド共和国 / アカシヤ共和国 | Akashiya | | Republic of Akashiya Land | Acacia |
| ラブリー連邦合衆国 / ラブリー国 / ラブリー合衆国 | Lovely | | Lovely Federal States | |
| こいつ＆あいつ国 / こいつ＆あいつ共和国 / こいつ＆あいつ連邦共和国 | Koitsu & Aitsu | | | |
| モアイ諸島首長国 / モアイ国 / モアイ首長国 | Moai | | Moai Islands Emirate | |
| パンダ茶会獣民共和国 / パンダ国 / パンダ獣民共和国 | Panda | | Panda Tea Party Beasts' Republic | |
| バウバウ国 | Bow-Wow | | Bow-Wow Nation | Bau Bau |
| ニャー帝国 | Nya Empire | | | Nyaa |
| ニャー大陸 | Nya Continent | | | |
| パロワールド | Paro World | | | |
| ２月７日島 | February 7th Island | | | |
| フランシス＝ペドロ島 | Francis-Pedro Island | | | |
| プリンス王国 | Prince Kingdom | | | |
| ファンファン要塞 | Fan-Fan Fortress | | | |
| グウェート地方 / グウェート | Gwait | | | Kuwait |
| リップチェイサー島 | Lip Chaser Island | | | |
| チンコココ＝カーン王国 | Chinkokoko-Kaan | | rude pun on purpose | |

## Items / skills / terms
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| ペンタ連合 | Penta Alliance | | the West | |
| アラジオ連合 | Aladio Alliance | | | |
| コイツ＆アイツ機構 | Koitsu & Aitsu Pact | | the East | |
| ウッキー | Ukki | | money, a monkey noise | |
| ネコ缶 / 猫缶 | cat food | | a can of it | |
| 聖はい / 聖盃 | Holy Grail | | treasure; really his cat food bowl | |
| 神の珠 | Divine Orb | | really a cat toy ball | |
| 神の箱 | Divine Box | | really a scratching stone | |
| 神のキバ / 神の牙 | Divine Fang | | really his can opener | |
| ピッコロミラー | Piccolo Mirror | | really his spoon | |
| 不老不死のつぼ | Urn of Immortality | | really catnip | |
| コルトランサー | Colt Lancer | | really his fork | |
| フェアリーソード | Fairy Sword | | really his knife | |
| 極上ロボ | Deluxe Robo / DX Robo | | Parodius' 極上, a unit class | |
| 国宝 | national treasure / treasure | | | |

## Menu terms (not enforced by the tool: labels are narrow)
Stats: 根性 Guts, 直感 Instinct, 命中 / 命中率 Accuracy, 海指 Sea Cmd, 陸指 Land Cmd, 空指 Air Cmd (海の指揮能力 Sea command, likewise land, air), 経験 EXP, レベル / ＬＶ Level / LV, 攻撃力 Attack, 守備力 Defense, 防御 Defense, 移動力 Move, 燃料 Fuel, 機数 Units, 射程 Range, 科学力 Science, お金 Money.
Commands: 攻撃 Attack, 移動 Move, 待機 Wait, 占領 Capture, 補給 Supply, 補充 Refill, 合流 Merge, 発進 Launch, 修復 Repair, 乗る Board, 交換 Swap, 一斉 All-out, 作戦 Plan, 情報 Info, お店 Shop, 機能 Options, 生産 Build, 出撃 Deploy, 部隊表 Unit List, 国情報 Nation Info, 全体マップ Full Map, ニャンＴＶ / NYANTV Nyan TV, 指揮官 Commander, 兵器 Weapon, 編成数 Formation, 保有数 Owned.
Ranks: 国王 King, 帝王 Emperor, 総統 Fuehrer, 大統領 President, 書記長 Gen. Sec. (flagged, 36 px), 首長 Emir, 党首 Leader, 総理 Prime Minister, 大帝王 Great Emperor, 国防長官 Defense Sec., 大将 General, 中将 Lt. General, 少将 Maj. General, 大佐 Colonel, 中佐 Lt. Colonel, 少佐 Major, 大尉 Captain, 中尉 1st Lt., 少尉 2nd Lt.
Items (`DATA/ITEM.BIN`, `PAW`, shop): ターボジェット Turbo Jet, フェニックスＤＸ Phoenix DX, ファイヤーストーム Firestorm, エレキラー Elekiller, ゴッドサービス God Service, トップガン Top Gun, 地雷 Mine, ワイドバズーカ Wide Bazooka, ターボエンジン Turbo Engine, ド根性玉 / ど根性玉 Guts Ball, レインボーショット Rainbow Shot, オーラボム Aura Bomb, ターボスクリュー Turbo Screw, ＩＣＢＭ ICBM, コークスクリュー Corkscrew, バリア Barrier.
Unit classes: 要撃機 Interceptor, 戦闘機 Fighter, 攻撃機 Attacker, 戦闘攻撃機 Fighter-Attacker, 攻撃ヘリ Attack Heli, 主力戦車 Main Tank, 軽戦車 Light Tank, 歩兵戦車 Infantry Tank, 自走対空砲 SP AA Gun, 機械化歩兵 Mech Infantry, 補給車 Supply Truck, 対空ミサイル AA Missile, 自走砲 SP Gun, 自走ロケット SP Rocket, 戦艦 Battleship, 駆逐艦 Destroyer, 空母 Carrier, 輸送艦 Transport, 潜水艦 Submarine, 極上ロボ DX Robo, 猫型決戦兵器 Cat Super Weapon, 秘密兵器 Secret Weapon, アイテム Item.

Commanders in `UNITINFO` are puns on real people (`ペンジェル・マンセル` Penigel Mansell, `ペンチウム・プロフェッサ` Pentium Professor, `クルシ～チョフ` Kurushchev): keep each pun's real-name shape.

## One-kanji table headers (12 px, flagged abbreviations)
建 Bd, 川 Rv, 道 Rd, 橋 Br, 氷 Ic, 雪 Sn, 海 Se, 岸 Cs, 岩 Rk, 砂 Sa, 土 Dt, 森 Fr, 草 Gr.

## Decisions from earlier batches
People: ベリアル・ブゥブゥー Belial Boo-Boo; コイツ/アイツ extended: そいつ Soitsu, どいつ Doitsu; ワン田 Wanda; メカニャンＮ号 Mecha-Nyan No. N.
Unit names (PAW table is the source; KABE4, bios and shouts follow): 紙ヒコーキ Paper Plane, イーグルサブロウシロウ Eagle Saburo-Shiro, ぷりぷりクフィル Bouncy Kfir, ビシバシＦ１ Bishi-Bashi F1, スケルス Stealthru, ビンビンダブル Vin-Vin Double, キレルンバ！ Kire-Rumba!, ブタシオ Salt Pork, メローラ Melora, バニーちゃん Bunny-chan, ヤッターバウ Yatter-Bow, ラッキー君 Lucky-kun, ビックサンダーモアイ Big Thunder Moai, コイツジャイアント Koitsu Giant, ペンタロウＸ Pentaro X, ニャイアントロボ Nyaiant Robo, ニャンダーバード Nyanderbird, ビックバイパー Vic Viper, ツインビー TwinBee (official Konami), リュウ弾 HE Shell.
Skills and misc: みきった Saw it coming, 鉄壁の守り Iron Wall, 軍事組織 Military Bloc, 民族 Ethnic Group, マス square, でちゅ tail `, chu`, タコ焼き takoyaki, 父ちゃん Pa.
Story names: チキィン Chikin, ブリンブリンＨ島 Bling-Bling H Island, 琉犬地方 Ryuken region, うすしおＦＣ Usushio FC, パロにゃんこ Paro Nyanko, ミカエル・アブゥ４世 Michael Abu IV, 最高主席 Supreme Chairman.
Held to one form although the Japanese varies: 神の爪 in `ENDING/TXT_END` stays Divine Fang (the same can opener), ニャー・ムーン in `P_NYAI` stays Nya-Mu. `P_NYAI` names him as in the Japanese, so the spoiler is the game's own.
Abbreviations forced by cell width are listed in `docs/tl-notes.md`.
