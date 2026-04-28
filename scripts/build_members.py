"""Build members.json from embedded data (no network needed)."""
import json
from datetime import datetime
from pathlib import Path

BASE = "https://images.microcms-assets.io/assets/5694fd90407444338a64d654e407cc0e/"

RAW = """kuzuha\t葛葉\tKuzuha\tJP\t2018-07-29\t72c4d4d190f14fb2b865a24596118ba2/liver-face_Kuzuha.png
salome-hyakumantenbara\t壱百満天原サロメ\tHyakumantenbara Salome\tJP\t2022-05-21\t58a505029c69440699d4e44416bba57d/liver-face_Salome_Hyakumantenbara.png.webp
kanae\t叶\tKanae\tJP\t2018-05-01\tba94d70307e344b083ca0b50fb733659/liver-face_Kanae.png
mito-tsukino\t月ノ美兎\tTsukino Mito\tJP\t2018-01-31\tbd287ec9cfb8453da4a32161e4e76ce1/liver-face_Mito_Tsukino.png.webp
vox-akuma\tヴォックス・アクマ\tVox Akuma\tEN\t2021-12-19\t75bce98aa25943518ae8b1d42ec3dd5d/liver-face_Vox_Akuma.png.webp
toya-kenmochi\t剣持刀也\tKenmochi Toya\tJP\t2018-03-14\tfa185ae5b61e4ed2ab59d3858e29229c/liver-face_Toya_Kenmochi.png.webp
sara-hoshikawa\t星川サラ\tHoshikawa Sara\tJP\t2019-10-16\tebb66fde318b469a8ef5bff61312730a/liver-face_Sara_Hoshikawa.png.webp
minato-fuwa\t不破湊\tFuwa Minato\tJP\t2019-11-27\t4b3624d691304879ac020c6ada8c7856/liver-face_Minato_Fuwa.png.webp
luca-kaneshiro\tルカ・カネシロ\tLuca Kaneshiro\tEN\t2021-12-19\ta69e253aceeb4ea2aad124963263d1f3/liver-face_Luca_Kaneshiro.png.webp
kaede-higuchi\t樋口楓\tHiguchi Kaede\tJP\t2018-01-31\ta10e6c0587a74e4781e3329c4ae732d6/liver-face_Kaede_Higuchi.png.webp
lauren-iroas\tローレン・イロアス\tLauren Iroas\tJP\t2021-07-21\t20a7002d409545f68b235f2dbadda706/liver-face_Lauren_Iroas.png
ange-katrina\tアンジュ・カトリーナ\tAnge Katrina\tJP\t2019-03-21\t15670f33fae545de9fc5dff585be332c/liver-face_Ange_Katrina.png
lize-helesta\tリゼ・ヘルエスタ\tLize Helesta\tJP\t2019-03-21\t47f33a1d55ff4c40aa815eaff1be3aab/liver-face_Lize_Helesta.png
toko-inui\t戌亥とこ\tInui Toko\tJP\t2019-03-21\te901f31dd23841438d5ed3113828353b/liver-face_Toko_Inui.png
shu-yamino\t闇ノシュウ\tShu Yamino\tEN\t2021-12-19\t57f8266ce45a4ace95f272c19e032413/liver-face_ShuYamino.png.webp
saku-sasaki\t笹木咲\tSasaki Saku\tJP\t2018-07-05\tcf45532cb7eb45bdb2789b3d3932f596/liver-face_Saku_Sasaki.png.webp
hayato-kagami\t加賀美ハヤト\tKagami Hayato\tJP\t2019-07-02\t616a31c054da4761ae731bc852f9381b/liver-face_Hayato_Kagami.png
kizuku-yashiro\t社築\tYashiro Kizuku\tJP\t2018-06-02\tff46243c3787455cb8005023513616ca/liver-face_Kizuku_Yashiro.png
lunlun\tルンルン\tLunlun\tJP\t2024-06-18\t21cd9392b3c24edcb8de8359286f7839/liver-face_Lunlun.png
ibrahim\tイブラヒム\tIbrahim\tJP\t2020-01-29\t4e6360c6d1994303ba0c0c5b753aa225/liver-face_Ibrahim.png
yuika-shiina\t椎名唯華\tShiina Yuika\tJP\t2018-07-29\t23ba0b2e138d45f6bdb6b94025377dc2/liver-face_Yuika_Shiina.png.webp
chima-machita\t町田ちま\tMachita Chima\tJP\t2018-08-30\t42d168bf6eca48e39031a2bbc6e666c6/liver-face_Chima_Machita.png
ars-almal\tアルス・アルマル\tArs Almal\tJP\t2019-07-23\t663f3aa8834241799f2449e8b393df17/liver-face_Ars_Almal.png
furen-e-lustario\tフレン・E・ルスタリオ\tFuren E Lustario\tJP\t2020-01-29\t217a9552d9544da2997dd017ac95b0ac/liver-face_Furen_E_Lustario.png.webp
ryushen\t緑仙\tRyushen\tJP\t2018-06-02\taa5e0be7f66c4c4e902a56f8bb2266b0/liver-face_Ryushen.png
kokoro-amamiya\t天宮こころ\tAmamiya Kokoro\tJP\t2019-08-07\t96874bf1074c477198deffe96d64c65e/liver-face_Kokoro_Amamiya.png.webp
himawari-honma\t本間ひまわり\tHonma Himawari\tJP\t2018-07-05\t977cdefa720e4035b71e580692316190/liver-face_Himawari_Honma.png
lulu-suzuhara\t鈴原るる\tSuzuhara Lulu\tJP\t2019-04-28\t78c0abc6efae46ea9d2bc98070866878/liver-face_Lulu_Suzuhara.png
alban-knox\tアルバーン・ノックス\tAlban Knox\tEN\t2022-02-26\tb55c850f56474b81876f9a678640ce52/liver-face_Alban_Knox.png.webp
akina-saegusa\t三枝明那\tSaegusa Akina\tJP\t2019-04-01\t110c847a4d9a4dc389758a66a408370b/liver-face_Akina_Saegusa.png.webp
haru-kaida\t甲斐田晴\tKaida Haru\tJP\t2020-04-01\tf5ac57e32d534ade918207d631b43b63/liver-face_Haru_Kaida.png.webp
elu\tえる\tElu\tJP\t2018-01-31\te749a2e50e1b4005b272260e9393d108/liver-face_Elu.png
meloco-kyoran\t狂蘭 メロコ\tMeloco Kyoran\tEN\t2022-12-05\t51ec419d0e4f4843a5a2385d908dcff8/liver-face_Meloco_Kyoran.png
nui-sociere\tニュイ・ソシエール\tNui Sociere\tJP\t2019-06-18\t4643fd371d974cdb93f07e9aa80d1fd0/liver-face_Nui_Sociere.png
chigusa-nishizono\t西園チグサ\tNishizono Chigusa\tJP\t2020-08-05\t63c5cc2c1c0546a6a8ea0617c182b849/liver-face_Chigusa_Nishizono.png.webp
uki-violeta\t浮奇・ヴィオレタ\tUki Violeta\tEN\t2022-02-26\ta3ad52e072e64b8294dee73c0618f00b/liver-face_Uki_Violeta.png
sango-suo\t周央サンゴ\tSuo Sango\tJP\t2020-08-05\t1df05d7e85a6468192f664ff258903f8/liver-face_Sango_Suo.png
enna-alouette\tエナー・アールウェット\tEnna Alouette\tEN\t2021-10-08\t0a0aec871e504f5c9eab69144afcd447/liver-face_Enna_Alouette.png.webp
kana-sukoya\t健屋花那\tSukoya Kana\tJP\t2019-09-19\t5b67649f6b7b4d84af278e4cce9532c9/liver-face_Kana_Sukoya.png.webp
debidebi-debiru\tでびでび・でびる\tDebidebi Debiru\tJP\t2018-08-30\t04f4ba87b763413da8836997ae3cd4c7/liver-face_Debidebi_Debiru.png.webp
ratna-petit\tラトナ・プティ\tRatna Petit\tJP\t2019-08-07\tcd5fe76cad754bc598421c15c5880c7b/liver-face_Ratna_Petit.png
hibari-watarai\t渡会雲雀\tWatarai Hibari\tJP\t2022-07-12\t65aa007678984a8ea3ff49da2c5f3260/liver-face_Hibari_Watarai.png.webp
sister-claire\tシスター・クレア\tSister Claire\tJP\t2018-06-02\t001f88b9145f495fb158d56550628e64/liver-face_Sister_Claire.png
marin-hayama\t葉山舞鈴\tHayama Marin\tJP\t2019-06-18\tf4a21638525f45b398f5b8e73fc558df/liver-face_Marin_Hayama.png
joe-rikiichi\tジョー・力一\tJoe Rikiichi\tJP\t2018-08-30\t4a3b9b71b6574bed8b6d5c08840ecdbe/liver-face_Joe_Rikiichi.png
rena-yorumi\t夜見れな\tYorumi Rena\tJP\t2019-07-02\tb889e7e0017d42d4986258b934978bc0/liver-face_Rena_Yorumi.png.webp
meme-mashiro\tましろ爻\tMashiro Meme\tJP\t2019-12-25\tdf5827d29d5a4bc38b0b8bb8bc79c1e2/liver-face_Meme_Mashiro.png.webp
mikoto-rindou\t竜胆尊\tRindou Mikoto\tJP\t2018-08-30\t1bf138f610fc48dda135b93ab9d93478/liver-face_Mikoto_Rindou.png.webp
makaino-ririmu\t魔界ノりりむ\tMakaino Ririmu\tJP\t2018-07-29\t4cdb61c4fc1545b38996ccb2296fc95a/liver-face_Ririmu_Makaino.png.webp
chaika-hanabatake\t花畑チャイカ\tHanabatake Chaika\tJP\t2018-06-02\te7a6cbdcfc9b40ea8ea8be29199becc7/liver-face_Chaika_Hanabatake.png.webp
ex-albio\tエクス・アルビオ\tEx Albio\tJP\t2019-05-17\t623ba1c69fd64308a4eb32efaa4a80d2/liver-face_Ex_Albio.png.webp
rion-takamiya\t鷹宮リオン\tTakamiya Rion\tJP\t2018-08-08\t3284cbdeda0e4bd8ad7d5fdfafc4623b/liver-face_Rion_Takamiya.png.webp
sonny-brisko\tサニー・ブリスコー\tSonny Brisko\tEN\t2022-02-26\t7951b32b19244128a2379a53fb8a9493/liver-face_Sonny_Brisko.png.webp
ren-zotto\tレン ゾット\tRen Zotto\tEN\t2022-07-24\tdeca5e8685ed481f8a618df234e5408c/liver-face_Ren_Zotto.png.webp
kei-nagao\t長尾景\tNagao Kei\tJP\t2020-04-01\t883ad7825d6141f1beb2f50b0a79f542/liver-face_Kei_Nagao.png
elira-pendora\tエリーラ ペンドラ\tElira Pendora\tEN\t2021-05-15\t3b0f859e100e419aa179bc9def264714/liver-face_Elira_Pendora.png.webp
leos-vincent\tレオス・ヴィンセント\tLeos Vincent\tJP\t2021-07-21\tfc61ee728a9949a4936c89be4a922e7c/liver-face_Leos_Vincent.png.webp
petra-gurin\tペトラ グリン\tPetra Gurin\tEN\t2021-07-18\tc11417fb94b04f27aaca9a698861286e/liver-face_Petra_Gurin.png.webp
belmond-banderas\tベルモンド・バンデラス\tBelmond Banderas\tJP\t2018-09-24\taf124abd3da043268dc7f59162d6e632/liver-face_Belmond_Banderas.png.webp
millie-parfait\tミリー・パフェ\tMillie Parfait\tEN\t2021-10-08\tfdf4cecc8af14d99a1d2c9f6acd4a6cb/liver-face_Millie_Parfait.png.webp
finana-ryugu\tフィナーナ 竜宮\tFinana Ryugu\tEN\t2021-05-15\t825b3215dd994a998e00c8efcecf49ce/liver-face_Finana_Ryugu.png.webp
fuyuki-hakase\t葉加瀬冬雪\tHakase Fuyuki\tJP\t2019-07-02\t041b493000c24f8d92adcc60ead539fb/liver-face_Fuyuki_Hakase.png
akira-shikinagi\t四季凪アキラ\tShinaginaki Akira\tJP\t2022-07-12\tde2e34f9584544fe882846f24947226e/liver-face_Akira_Shikinagi.png.webp
maria-marionette\tマリア マリオネット\tMaria Marionette\tEN\t2022-07-24\te4d32f8f3a9e4efc852950d38ea4ba57/liver-face_Maria_Marionette.png.webp
rou-koyanagi\t小柳ロウ\tKoyanagi Rou\tJP\t2023-04-25\t2222cb2866fe4f3b9c85a45f3689fe53/liver-face_Rou_Koyanagi.png
keisuke-maimoto\t舞元啓介\tMaimoto Keisuke\tJP\t2018-08-08\t62cb2dc53c984daaac6cf0d398415364/liver-face_Keisuke_Maimoto.png
tomoe-shirayuki\t白雪巴\tShirayuki Tomoe\tJP\t2019-11-27\td5a34b5834374e50a289198280aad119/liver-face_Tomoe_Shirayuki.png
lain-paterson\tレイン・パターソン\tLain Paterson\tJP\t2021-07-21\tda6c50863a1247ff92ab8246d88a4145/liver-face_Lain_Paterson.png.webp
ruri-shioriha\t栞葉るり\tShioriha Ruri\tJP\t2023-11-20\ta1334987716b45f0875d3ac8c8dd0593/liver-face_Ruri_Shioriha.png
sho-hoshirube\t星導ショウ\tHoshirube Sho\tJP\t2023-04-25\t4b2b45a06a2a49e3b6c6835087ecc1b2/liver-face_Sho_Hoshirube.png
kou-uzuki\t卯月コウ\tUzuki Kou\tJP\t2018-06-02\taf6b8193430741f8b5633a2ffa4ab9dc/liver-face_Kou_Uzuki.png.webp
tamaki-fumino\t文野環\tFumino Tamaki\tJP\t2018-03-14\t362f946246d049ada0e4e88410ace52e/liver-face_Tamaki_Fumino.png.webp
shellin-burgundy\tシェリン・バーガンディ\tShellin Burgundy\tJP\t2019-09-19\t9be70f7ce3534a908efce63118bb7fef/liver-face_Shellin_Burgundy.png.webp
riri-yuhi\t夕陽リリ\tYuhi Riri\tJP\t2018-03-14\tf9bfdda16f1f46159faf7965894c9a1e/liver-face_Riri_Yuuhi.png
rin-shizuka\t静凛\tShizuka Rin\tJP\t2018-01-31\t3e388baf964c4c4a84b27cd709f86ce4/liver-face_Rin_Shizuka.png.webp
seraph-dazzlegarden\tセラフ・ダズルガーデン\tSeraph Dazzlegarden\tJP\t2022-07-12\t42fb181000564635aab64bb7cbedb886/liver-face_Seraph_Dazzlegarden.png.webp
kanato-fura\t風楽奏斗\tFura Kanato\tJP\t2022-07-12\tb0151287da7d40e4b3d80ce499838785/liver-face_Kanato_Fura.png.webp
mana-hibachi\t緋八マナ\tHibachi Mana\tJP\t2023-03-29\tc1a94fff322a4796833eca994d9d0bf5/liver-face_Mana_Hibachi.png
tojiro-genzuki\t弦月藤士郎\tGenzuki Tojiro\tJP\t2020-04-01\tee4d153e3ebd4dc8aa7a2d1af6b65a3e/liver-face_Tojiro_Genzuki.png
sophia-valentine\tソフィア・ヴァレンタイン\tSophia Valentine\tJP\t2023-01-15\t6489a08fe04c4bfc9e77e652f664ac66/liver-face_Sophia_Valentine.png
nozomi-ishigami\t石神のぞみ\tIshigami Nozomi\tJP\t2023-01-15\te1a09f9b02084889a165541da18a6c14/liver-face_Nozomi_Ishigami.png
rai-inami\t伊波ライ\tInami Rai\tJP\t2023-04-25\t177564c99e734028b8a59f318b333c33/liver-face_Rai_Inami.png
ittetsu-saiki\t佐伯イッテツ\tSaiki Ittetsu\tJP\t2023-03-29\t36b63b547d2a4facad876cc40f0736a0/liver-face_Ittetsu_Saiki.png
toru-koshimizu\t小清水透\tKoshimizu Toru\tJP\t2023-01-15\t922486712e7140f5abf2ba415c8a574a/liver-face_Toru_Koshimizu.png
kakeru-yumeoi\t夢追翔\tYumeoi Kakeru\tJP\t2018-09-24\ta14d762a2d674b599d530083fcd49447/liver-face_Kakeru_Yumeoi.png.webp
levi-elipha\tレヴィ・エリファ\tLevi Elipha\tJP\t2019-05-17\ta2d250273e0f4146990ebac2d5d1ce8d/liver-face_Levi_Elipha.png.webp
kagetsu-murakumo\t叢雲カゲツ\tMurakumo Kagetsu\tJP\t2023-04-25\t44eb7fa3087b480dad1ae245db21952e/liver-face_Kagetsu_Murakumo.png
dola\tドーラ\tDola\tJP\t2018-06-02\t2a755bcce89344fbbc50d336af45efd3/liver-face_Dola.png
gaku-fushimi\t伏見ガク\tFushimi Gaku\tJP\t2018-03-14\t4834edc2a7c9472ea9d6fe4ee43c2a04/liver-face_Gaku_Fushimi.png.webp
scarle-yonaguni\tスカーレ ヨナグニ\tScarle Yonaguni\tEN\t2022-07-24\ta410b878c4f64e9a9d1577097e3e56d9/liver-face_Scarle_Yonaguni.png.webp
oliver-evans\tオリバー・エバンス\tOliver Evans\tJP\t2021-07-21\tad3beeb99c4a4482a90d1a567648450e/liver-face_Oliver_Evans.png
kaisei\t魁星\tKaisei\tJP\t2024-03-11\tc531381ae7554535b16a266bbb3d3729/liver-face_Kaisei.png
rito-usami\t宇佐美リト\tUsami Rito\tJP\t2023-03-29\tb7b9c49fc81440efb0b3fbf29faad4ce/liver-face_Rito_Usami.png
roa-yuzuki\t夢月ロア\tYuzuki Roa\tJP\t2019-01-18\tdc2fe6896dcd4b77bfb89f60f4a588e8/liver-face_Roa_Yuzuki.png.webp
kazaki-morinaka\t森中花咲\tMoninaka Kazaki\tJP\t2018-03-14\t3e3e5fefe79c47fe8bfb9601fd027376/liver-face_Kazaki_Morinaka.png.webp
ness-sakaki\t榊ネス\tSakaki Ness\tJP\t2024-03-11\t3c3a4035d9a2410481bd59b3d6a99bb9/liver-face_Ness_Sakaki.png
masaru-suzuki\t鈴木勝\tSuzuki Masaru\tJP\t2018-06-02\t21a992f2a13c450caa01eed8bf092868/liver-face_Masaru_Suzuki.png.webp
akari-shishido\t獅子堂あかり\tShishido Akari\tJP\t2023-01-15\te44d14200fec437eb35361aab7e29e76/liver-face_Akari_Shishido.png
wen-akagi\t赤城ウェン\tAkagi Wen\tJP\t2023-03-29\td35a7ec3da38468c8830eaf9f0a51c4c/liver-face_Wen_Akagi.png
rika-igarashi\t五十嵐梨花\tIgarashi Rika\tJP\t2023-01-15\ta5dc528f536b4c7eaf06fadca75013d8/liver-face_Rika_Igarashi.png
yang-nari\tヤン ナリ\tYang Nari\tJP\t2020-10-14\taafac3ee207e439aa4a736c230fac310/liver-face_Yang_Nari.png.webp
hisui-kitakoji\t北小路ヒスイ\tKitakoji Hisui\tJP\t2020-08-05\tb9d1759ea04d47ebb5503f1d4b66688b/liver-face_Hisui_Kitakoji.png
nana-tamanoi\t珠乃井ナナ\tTamanoi Nana\tJP\t2024-06-18\tf76ae3abb42440108fb75605bdd764e7/liver-face_Nana_Tamanoi.png
mao-matsukai\t魔使マオ\tMatsukai Mao\tJP\t2019-10-31\t247b9af77e04473091ee72acbf259fa4/liver-face_Mao_Matsukai.png
nei-ponto\t先斗寧\tPonto Nei\tJP\t2022-03-16\t08a0455940404ccfa11a8c9d6a4538ad/liver-face_Nei_Ponto.png
vantacrow-bringer\tベンタクロウ ブリンガー\tVantacrow Bringer\tEN\t2023-06-21\td35ae95c701a41dfb191ba04f5d6e05f/liver-face_Vantacrow_Bringer.png
shiba-kuroi\t黒井しば\tKuroi Shiba\tJP\t2018-09-24\t63a01a3e31514430b203b973aa97f22e/liver-face_Shiba_Kuroi.png.webp
sou-hayase\t早瀬走\tHayase Sou\tJP\t2019-09-19\t79033e0bc6ef4db3b4d24abde3fddcc9/liver-face_Sou_Hayase.png.webp
aia-amare\tアイア アマレ\tAia Amare\tEN\t2022-07-24\t277243c23e434832abb4d2eb80db5ad9/liver-face_Aia_Amare.png.webp
mugi-ienaga\t家長むぎ\tIenaga Mugi\tJP\t2018-03-14\t7a2a96dda3af40afbb54d5e7af2e5955/liver-face_Mugi_Ienaga.png.webp
karuta-yamagami\t山神カルタ\tYamagami Karuta\tJP\t2019-10-16\t6d5442e6ebd64412ae714901c0669487/liver-face_Karuta_Yamagami.png
hana-macchia\tハナ マキア\tHana Macchia\tJP\t2019-09-13\tfb0035ee1e374daf9f57a6589468dced/liver-face_Hana_Macchia.png
ritsuki-sakura\t桜凛月\tSakura Ritsuki\tJP\t2018-08-30\t3b53416aa270464f994b3a88f65ec79b/liver-face_Ritsuki_Sakura.png.webp
fumi\tフミ\tFumi\tJP\t2019-10-16\t2aecf7a5282e4a349ead29f8f8e525f1/liver-face_Fumi.png.webp
meruto-kuramochi\t倉持めると\tKuramochi Meruto\tJP\t2023-01-15\t6da2c0ebc0e84b3da6c1a410379b8346/liver-face_Meruto_Kuramochi.png
shoichi-kanda\t神田笑一\tKanda Shoichi\tJP\t2018-08-08\t54c64c3432ff45e683af0ada04908535/liver-face_Shoichi_Kanda.png.webp
milan-kestrel\tミラン・ケストレル\tMilan Kestrel\tJP\t2023-11-20\t21f60a123e9d470383170b1ebb85914b/liver-face_Milan_Kestrel.png
yusei-kitami\t北見遊征\tKitami Yusei\tJP\t2024-03-11\tfa69680e8c48481d9d290762430a381d/liver-face_Yusei_Kitami.png
yotsuha-umise\t海妹四葉\tUmise Yotsuha\tJP\t2022-03-16\ta4633f90873b4427843f95ee84970b8a/liver-face_Yotsuha_Umise.png.webp
alice-mononobe\t物述有栖\tMononobe Alice\tJP\t2018-03-14\t8b1feefa2107498da11f9c6ec559b415/liver-face_Alice_Mononobe.png.webp
suzuna-nanase\t七瀬すず菜\tNanase Suzuna\tJP\t2024-08-12\tdf041caab67b41a0b7539c054e10294a/liver-face_Suzuna_Nanase.png
doppio-dropscythe\tドッピオ ドロップサイト\tDoppio Dropscythe\tEN\t2022-12-05\t44d559377a9649ddb85df12fcab6421e/liver-face_Doppio_Dropscythe.png
natsume-kurusu\t来栖夏芽\tKurusu Natsume\tJP\t2019-12-25\tef419dca96cd46af9511ee6393562dfe/liver-face_Natsume_Kurusu.png.webp
luis-cammy\tルイス・キャミー\tLuis Cammy\tJP\t2019-10-31\t91e3108fec9e4cf4b632c4c76a060c7b/liver-face_Luis_Cammy.png
trout-nagisa\t渚トラウト\tNagisa Trout\tJP\t2024-08-12\t03ab673bb8c0400a9fdce1f51755a7e7/liver-face_Trout_Nagisa.png
berry-saotome\t早乙女ベリー\tSaotome Berry\tJP\t2024-08-12\t712d2034f4d24f29ae34ffaf8b55f46a/liver-face_Berry_Saotome.png
roco-kaburaki\t鏑木ろこ\tKaburaki Roco\tJP\t2023-01-15\tc1cec4b0ed294941a115cffa01b0c203/liver-face_Roko_Kaburaki.png
eli-conifer\tエリー・コニファー\tEli Conifer\tJP\t2019-08-07\t40723eda291747c58e4c148334ea95d4/liver-face_Eli_Conifer.png.webp
ver-vermillion\tヴェール ヴァーミリオン\tVer Vermillion\tEN\t2022-12-05\tf0b609dfe4e84993ba2960c8c7fca9f5/liver-face_Ver_Vermillion.png
yu-q-wilson\tユウ Q ウィルソン\tYu Q. Wilson\tEN\t2023-06-21\td0ee818c0be94a03836c33a5e54dc091/liver-face_Yu_Q._Wilson.png
seffyna\tセフィナ\tSeffyna\tJP\t2021-04-30\tb1a1d6c519e94e458d216b027f37ceee/liver-face_Seffyna.png
soma-sakayori\t酒寄颯馬\tSakayori Soma\tJP\t2024-08-12\t9bb7b450ba15434aad0b137ad0b4232f/liver-face_Soma_Sakayori.png
emma-august\tえま★おうがすと\tEmma August\tJP\t2019-10-31\tb9ee06612e6647159a40a668b8d602e4/liver-face_Emma_August.png
vezalius-bandage\tヴェザリウス バンデージ\tVezalius Bandage\tEN\t2023-06-21\td82003529a8f472c825834942a43c98a/liver-face_Vezalius_Bandage.png
kaelix-debonair\tケイリクス・デボネア\tKaelix Debonair\tEN\t2025-03-12\t6d3794aa4a0b46de802ee1dda99dc0df/liver-face_Kaelix_Debonair.png
riko-shiga\t司賀りこ\tShiga Riko\tJP\t2024-06-18\t7a0d6f47b7bc4785b570386b748d1b8e/liver-face_Riko_Shiga.png
sayo-amemori\t雨森小夜\tAmemori Sayo\tJP\t2018-08-08\ta6e0e401536542db95ed616a038d5d6f/liver-face_Sayo_Amemori.png.webp
mahiro-yukishiro\t雪城眞尋\tYukishiro Mahiro\tJP\t2019-04-28\tef95a4f652d644889603b8ddd29f2f0b/liver-face_Mahiro_Yukishiro.png
youko-akabane\t赤羽葉子\tAkabane Youko\tJP\t2018-05-01\tc921440e235d419ab515e49a46ec0648/liver-face_Yoko_Akabane.png
kirame-sorahoshi\t空星きらめ\tSorahoshi Kirame\tJP\t2020-06-30\t61254e647cfb4edea5bb19a5f1ec90d7/liver-face_Kirame_Sorahoshi.png.webp
kohaku-todo\t東堂コハク\tTodo Kohaku\tJP\t2020-08-05\t4c6791bb45cc4c5087eb2ce96a63fa9a/liver-face_Kohaku_Todo.png.webp
gilzaren-iii\tギルザレンⅢ世\tGilzaren III\tJP\t2018-03-14\tfc45c528d4ad49ae992ccf99c9e27deb/liver-face_Gilzaren_%E2%85%A2.png
ayato-hitotsubashi\t一橋綾人\tHitotsubashi Ayato\tJP\t2025-04-10\t2629dbb7346d4ec8827dec1ee894e5e8/liver-face_Ayato_Hitotsubashi.png
kisara\t綺沙良\tKisara\tJP\t2024-06-18\ta5e303fc14b94d74bda56acdb673620b/liver-face_Kisara.png
air-harusaki\t春崎エアル\tHarusaki Air\tJP\t2018-06-07\t4961a4b80e264badaa2d8bbb699c992e/liver-face_Air_Harusaki.png.webp
rine-yaguruma\t矢車りね\tYaguruma Rine\tJP\t2018-09-24\te11a9833e0224a1e9a17c5f3eacfda5b/liver-face_Rine_Yaguruma.png
ichigo-ushimi\t宇志海いちご\tUshimi Ichigo\tJP\t2018-03-14\t3007bd76572d42f19efd70a1f168ebc4/liver-face_Ichigo_Ushimi.png.webp
freodore\tフリオドール\tFreodore\tEN\t2025-03-12\te62e2f857c8e46fc98c79bdf9bb848bd/liver-face_Freodore.png
manami-aizono\t愛園愛美\tAizono Manami\tJP\t2019-04-01\t5af8b71bbf0240db97c2345e13ec7f58/liver-face_Manami_Aizono.png
min-suha\tミン スゥーハ\tMin Suha\tJP\t2020-01-24\t5e8e5c93e7fe4d3eb30b14ffe6581ef0/liver-face_Suha_Min.png.webp
zeal-ginjoka\tジール・ギンジョウカ\tZeal Ginjoka\tEN\t2025-03-12\t0e8b5902726d43babafc6f2623c76be5/liver-face_Zeal_Ginjoka.png
tamako-kirara\t雲母たまこ\tKirara Tamako\tJP\t2024-08-12\te3730f9f6b6f4428a0f5d9d135e0b1f8/liver-face_Tamako_Kirara.png
seible\tセイブル\tSeible\tEN\t2025-03-12\ta8766bf970164d168b02dbd7ce635abc/liver-face_Seible.png
toto-tachitsute\t立伝都々\tTachitsute Toto\tJP\t2023-11-20\tbf7e7bc838da450bbe4d875eba2e263e/liver-face_Toto_Tachitsute.png
hajime-shibuya\t渋谷ハジメ\tShibuya Hajime\tJP\t2018-01-31\t48d793b718984df8b9f81ade7f0b8a5a/liver-face_Hajime_Shibuya.png.webp
claude-clawmark\tクロード クローマーク\tClaude Clawmark\tEN\t2023-10-25\t9a3e3897cd36495cb28868a355506527/liver-face_Claude_Clawmark.png
sakyo-itsuki\t五木左京\tItsuki Sakyo\tJP\t2025-04-10\t3e196e23ad234fc39212007f10fa046d/liver-face_Sakyo_Itsuki.png
kyoko-todoroki\t轟京子\tTodoroki Kyoko\tJP\t2018-06-02\t72d24f8d5950414294f799c85542681f/liver-face_Kyoko_Todoroki.png
moira\tモイラ\tMoira\tJP\t2018-01-31\tea9f478820c84208840d248d5c6610d1/liver-face_Moira.png.webp
mone-kozue\t梢桃音\tKozue Mone\tJP\t2024-06-18\tc2b3cb15c4374087b1e5c2d306326583/liver-face_Mone_Kozue.png
muyu-amagase\t天ヶ瀬むゆ\tAmagase Muyu\tJP\t2022-03-16\t93ac3fe993a4417987e983c31c972da8/liver-face_Muyu_Amagase.png.webp
ha-yun\tハ ユン\tHa Yun\tJP\t2021-08-31\t4a89b0fe3c2a42d1912d6f053a766264/liver-face_Ha_Yun.png
miku-nekoyashiki\t猫屋敷美紅\tNekoyashiki Miku\tJP\t2025-08-13\t365b8ecc7fa74048841d38f4b21a07e6/liver-face_Miku_Nekoyashiki.png
tsumugu-kataribe\t語部紡\tKataribe Tsumugu\tJP\t2019-01-27\ta3ece7130cf946c69697c7a4105b9a77/liver-face_Tsumugu_Kataribe.png.webp
isumi-shirose\t城瀬いすみ\tShirose Isumi\tJP\t2025-09-16\tc359f30b042746be88cd87f76bd49894/liver-face_Isumi_Shirose.png
hina-asuka\t飛鳥ひな\tAsuka Hina\tJP\t2018-08-08\td6f703f463bd4882abf19872d5897ea4/liver-face_Hina_Asuka.png.webp
madoka-minamo\t水面まどか\tMinamo Madoka\tJP\t2026-01-28\t4b9fcaf98c0d4b7f91e2c1ab9be7985b/liver-face_Madoka_Minamo.png
lee-roha\tイ ロハ\tLee Roha\tJP\t2020-08-06\t0901bc3c2c534410a60d82ac7ad347d1/liver-face_Roha_Lee.png
ayane-shirasa\t白砂あやね\tShirasa Ayane\tJP\t2026-01-28\td61c28ffcf8a420aafbaca7d0769b07f/liver-face_Ayane_Shirasa.png
reo-sumeragi\t皇れお\tSumeragi Reo\tJP\t2025-09-16\t7965aa35528c4bb2918ce13b44f78ea8/liver-face_Reo_Sumeragi.png
klara-charmwood\tクララ チャームウッド\tKlara Charmwood\tEN\t2024-05-20\tf20391e06870486ca53c6c90b39b4c13/liver-face_Klara_Charmwood.png
mikaru-kadou\t蝸堂みかる\tKadou Mikaru\tJP\t2025-08-13\t2fabd91950cc46d19be06392a8654708/liver-face_Mikaru_Kadou.png
tsubasa-hanakago\t花籠つばさ\tHanakago Tsubasa\tJP\t2025-09-16\tfcd6581ea328412e99cd953e80ae738d/liver-face_Tsubasa_Hanakago.png
nonoha-togawa\t十河ののは\tTogawa Nonoha\tJP\t2025-08-13\tda656750c9204df59abf3ba0a84cf56c/liver-face_Nonoha_Togawa.png
yuno-shinomiya\t篠宮ゆの\tShinomiya Yuno\tJP\t2025-09-16\t5fa8e0b57d7c4b8fac7ec953105e0708/liver-face_Yuno_Shinomiya.png
so-nagi\tソ ナギ\tSo Nagi\tJP\t2020-06-01\t2a11c3b58b16417080e1f408585d4783/liver-face_So_Nagi.png
layla-alstroemeria\tライラ アルストロエメリア\tLayla Alstroemeria\tJP\t2020-03-15\t6aacb7c7f40c4d558b3384a026f55402/liver-face_Layla_Alstroemeria.png.webp
reina\tRei7\tReina\tJP\t2026-04-18\td52c689962e940d2b422753e0fecd744/liver-face_Rei7.png
ryoma-barrenwort\t凉舞 バレンウォート\tRyoma Barrenwort\tEN\t2024-05-20\t0576be0e5a0c44c2a44d761f29a4e84c/liver-face_Ryoma_Barrenwort.png
kotone-mikogami\t御子神琴音\tMikogami Kotone\tJP\t2026-04-18\tea9e654925fe4b5ab70f75ed5c9bec16/liver-face_Kotone_Mikogami.png
rayon\tレヨン\tRayon\tJP\t2026-04-18\t29d0df78c9b241ebbfd6a0dc3f1590ff/liver-face_Rayon.png
shino-yagyu\t夜牛詩乃\tYagyu Shino\tJP\t2025-08-13\td712a24a2b8543e0b589ecdfbe7c5ad9/liver-face_Shino_Yagyu.png
daichi-tsukahara\t塚原大地\tTsukahara Daichi\tJP\t2026-04-18\t076a419e60b243f484fdb1f076dae6d3/liver-face_Daichi_Tsukahara.png
ayumu-senri\t千凛あゆむ\tSenri Ayumu\tJP\t2026-04-18\te44c5e13ac324cd3a1b43196739bea2f/liver-face_Ayumu_Senri.png
na-sera\tナ セラ\tNa Sera\tJP\t2021-08-31\t40bc06403098465284d410b6ee21d3e2/liver-face_Na_Sera%20(1).png
etna-crimson\tエトナ クリムソン\tEtna Crimson\tJP\t2020-08-07\t4e21d893925f4f92a2730c28c71b49dd/liver-face_Etna_Crimson.png.webp
oh-jiyu\tオ ジユ\tOh Jiyu\tJP\t2020-10-14\te738023c6a744910b52baee0f2b4fcb3/liver-face_Jiyu_Oh.png.webp
onotora\t男虎\tOnotora\tJP\t2026-04-18\t9b5cbb18f0eb42af9f738683d7551cfa/liver-face_Onotora.png
akira-ray\t明楽レイ\tAkira Ray\tJP\t2020-08-06\t353657a3d45540098b20eff2112308be/liver-face_Ray_Akira.png.webp
rai-galilei\tライ ガリレイ\tRai Galilei\tJP\t2019-12-18\tf8223e6b3b4441bb81ecaf85512b33ca/liver-face_Rai_Galilei.png.webp
gaon\tガオン\tGaon\tJP\t2020-01-24\t9619eff7b9114d59a6f348a0b82707ab/liver-face_Gaon.png
iruka-kokonami\t小々波いるか\tKokonami Iruka\tJP\t2026-04-18\t3e5aada39e0f454288790ffa63e4e3f3/liver-face_Iruka_Kokonami.png
derem-kado\tデレム カド\tDerem Kado\tJP\t2020-11-13\tdd96bf7da87140e0933208d93a664cec/liver-face_Derem_Kado.png
eita-kuri\t九里詠太\tKuri Eita\tJP\t2026-04-18\tda61cb3994204a2f8d6e787fca22c134/liver-face_Eita_Kuri.png
ryu-hari\tリュ ハリ\tRyu Hari\tJP\t2020-10-14\t07ac1f96aa024d99addc251cec709635/liver-face_Hari_Ryu.png.webp
nagisa-arcinia\tナギサ アルシニア\tNagisa Arcinia\tJP\t2020-11-13\t3cf844c4212f463fa512c1c6c27a02fd/liver-face_Nagisa_Arcinia.png.webp
yog\t尤格\tYog\tVR\t2021-09-24\t45205d834d844e84888716570e5d9a7b/liver-face_Yog.png
nanami\t七海\tNanami\tVR\t2019-06-11\t261d37057554476aa036967a5a1c5248/liver-face_Nanami.png.webp
eine\t艾因\tEine\tVR\t2019-05-06\t096a6c4a5bef41798cd482bad96ea96a/liver-face_Eine.png.webp
aza\t阿萨\tAza\tVR\t2019-11-20\t45880475d7fb40a0be425b5f46417643/liver-face_Aza.png.webp
yagi\t八木迪之\tYagi\tVR\t2019-11-20\t542ec9849a1a41f884eede1a5d09ffa1/liver-face_Yagi.png.webp
tabibito\t度人\tTabibito\tVR\t2019-11-20\t98d49949f4c3426f99b91b98016b94f9/liver-face_Tabibito.png.webp
michiya\t未知夜\tMichiya\tVR\t2023-06-01\t7312205e9eef488ea7d82d300a8e2073/liver-face_Michiya.png
ameki\t雨纪\tAmeki\tVR\t2023-06-01\ta3e370d5db504b16b761bba379c1a301/liver-face_Ameki.png
ayumi\t入福步\tAyumi\tVR\t2023-08-25\tbaea4fdc9aa74e82a13794985b7aa8c7/liver-face_Ayumi.png
urushiha\t漆羽\tUrushiha\tVR\t2023-08-25\td859dea99d294da6b94521ab644fa0ea/liver-face_Urushiha.png
richi\t离枝\tRichi\tVR\t2023-08-25\tc3a6ccb936034a8dba31990fd1f5382e/liver-face_Richi.png
mizuki\t弥月\tMizuki\tVR\t2023-08-25\tcfac97b19505480dbc73a16aa49f2167/liver-face_Mizuki.png
mit3uri\t三理\tMit3uri\tVR\t2025-02-28\tb1a90958c8d64ba198749c6d83706f81/liver-face_Mit3uri.png
melody\t泽音\tMelody\tVR\t2025-01-16\tb56598fb7adb4776a6b4354d6440fd04/liver-face_Melody.png
yua\t悠亚\tYua\tVR\t2020-09-20\tfac8e617a29042f59c59bd521ccb78d3/liver-face_Yua.png.webp
chiharu\t千春\tChiharu\tVR\t2020-07-20\t526768a3844e4c83b29f4df3c2cb6547/liver-face_Chiharu.png.webp
saya\t沙夜\tSaya\tVR\t2020-01-14\t0b49792ba797429b88156fc05bc67b95/liver-face_Saya.png.webp
yukie\t雪绘\tYukie\tVR\t2020-01-14\t8448a32ad4c042c182fbe8d885a3dc2c/liver-face_Yukie.png.webp
nimue\t妮慕\tNimue\tVR\t2025-02-28\t4c1dd2cc91604aeba58bda7ae597d4f7/liver-face_Nimue.png
kioi\t柚雨\tKioi\tVR\t2025-08-01\tdc5f62b8770d48f5837ea451327787c4/liver-face_Kioi.png
hunger\t暴食\tHunger\tVR\t2021-09-24\teb8bf7e87e18465ba283cef6d539aede/liver-face_Hunger.png.webp
sybil\t希维\tSybil\tVR\t2022-01-02\t5ec4c743af2d45a5bd8a2cdb987c5816/liver-face_Sibil.png
waku\t惑姫\tWaku\tVR\t2019-09-16\td66c850d52864249a5c6baeb8265aa8f/liver-face_Waku.png.webp
kouichi\t光一\tKouichi\tVR\t2019-06-11\t4d9a67a52983443f9bafafcece1434c0/liver-face_Kouichi.png.webp
tocci\t桃星\tTocci\tVR\t2021-05-01\tc364ec5d83194ad9b4edd033fe89e5dc/liver-face_Tocci.png
mayumi\t勾檀\tMayumi\tVR\t2021-03-04\t44cc258438b744d8b08748669ff24aef/liver-face_Mayumi.png.webp
kiti\t吉吉\tKiti\tVR\t2021-05-01\t9ff4528e4f8f4e6a98c1a9e7d4ca54e4/liver-face_Kiti.png.webp
awu\t哎小呜\tAwu\tVR\t2023-06-01\t07878ae182ac4a339e407972d2ac360e/liver-face_Awu.png
hatsuse\t初濑\tHatsuse\tVR\t2023-06-01\t5f9aa5f0376a4d498df3e41b3d68cf4e/liver-face_Hatsuse.png
hajime\t晴一\tHajime\tVR\t2023-08-25\td18c05798d734ed4810157b71d2837fa/liver-face_Hajime.png
mikoto\t蜜言\tMikoto\tVR\t2023-08-25\t6ccbde6d4e6d4d738468b15c8d03509a/liver-face_Mikoto.png
harei\t花礼\tHarei\tVR\t2024-07-10\t7f5223d95956498cba7a42bbf6e4bfa7/liver-face_Harei.png
kima\t鬼间\tKima\tVR\t2024-05-05\t9736984b50b4429fb3e4ea0a307b6cf6/liver-face_Kima.png
girimi\t雾深\tGirimi\tVR\t2022-01-02\t6c6b6d75ff8e447db8a024c7184ad8f4/liver-face_Girimi.png.webp
chiyuu\t千幽\tChiyuu\tVR\t2020-12-05\t275a8b92d6e8475c8911978322ebd4db/liver-face_Chiyuu.png.webp
shaun\t勺\tShaun\tVR\t2020-09-20\t04f0e3f8911140028d0fdf7e36ecb063/liver-face_Shaun.png
rhea\t瑞娅\tRhea\tVR\t2021-07-19\tf02de8db255d46c6861066b58f231eaa/liver-face_Rhea.png
leo\t莱恩\tLeo\tVR\t2022-08-22\td3722e05610845849dbaa90822cb6cf4/liver-face_Leo.png
shiori\t栞栞\tShiori\tVR\t2023-01-25\t02067d1eb6b24429aa94c1fafe1e5621/liver-face_Shiori.png
sui\t岁己\tSui\tVR\t2022-08-22\t27ae81af8bbb43ee84867d6e9946eb4a/liver-face_Sui.png
yukisyo\t雪烛\tYukisyo\tVR\t2023-11-30\t3f3b14474d77404888506e06703a0479/liver-face_Yukisyo.png
nagisa\t米汀\tNagisa\tVR\t2023-11-30\t052bf04baef045e898900f4a1831d749/liver-face_Nagisa.png
pako\t帕可\tPako\tVR\t2023-11-30\t89a5213170134fedab53532d419cd8c0/liver-face_Pako.png
susu\t点酥\tSusu\tVR\t2024-07-10\t68b2686a13e74e819c071b4e22e7b99b/liver-face_Susu.png
momoka\t桃代\tMomoka\tVR\t2024-07-10\t6b7be32474cc42108032b448e3bf4273/liver-face_Momoka.png
meme\t沐毛\tMeme\tVR\t2025-02-28\t7804960d092e46e48f39b175db9590e6/liver-face_Meme.png
nori\t能能\tNori\tVR\t2025-08-01\t64ec8e567fc34e3faa6a7dda24af1c91/liver-face_Nori.png
mei\t命依\tMei\tVR\t2025-02-28\t39b2caf0e9674f1093f6607ecaf7d97b/liver-face_Mei.png
mofu\t犬绒\tMofu\tVR\t2025-08-01\t62b38b68564648b492d74bd3f04e9f30/liver-face_Mofu.png"""

def main():
    members = []
    for line in RAW.strip().splitlines():
        parts = line.split("\t")
        if len(parts) != 6:
            print(f"SKIP bad line: {line[:60]}")
            continue
        mid, name, nameEn, branch, debut, imgpath = parts
        members.append({
            "id": mid,
            "name": name,
            "nameEn": nameEn,
            "branch": branch,
            "debutDate": debut,
            "image": BASE + imgpath,
            "active": True,
        })

    members.sort(key=lambda m: m["debutDate"] or "9999")

    out_path = Path(__file__).parent.parent / "data" / "members.json"
    out_path.parent.mkdir(exist_ok=True)
    payload = {"lastUpdated": datetime.now().strftime("%Y-%m-%d"), "members": members}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"✓ Written {len(members)} members to {out_path}")

if __name__ == "__main__":
    main()
