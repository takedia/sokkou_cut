# 側溝カットガイド（Cutcalc）— ファイル構成・運用メモ

カメラのガイド線で側溝などの**切断角度・切断長**を読み取り、面（底面・面取り）の**ずらし値**まで計算する単一HTMLアプリ。

## 公開・配布
- **Web（GitHub Pages）**: リポジトリ `takedia/sokkou_cut`、公開元ブランチ **workmain**。
  - 実体ページ: `https://takedia.github.io/sokkou_cut/cutcalc.html`（`index.html` はリポジトリ管理外＝ローカルプレビュー専用）
  - `work` ブランチは workmain のバックアップミラー（基本同一）。
- **Androidアプリ**: `C:\Users\ipconfig\AndroidStudioProjects\CutCalc`（package `com.hac.ucutguide`）。
  - WebViewで `assets/cutcalc.html` を表示。**assets に cutcalc.html / i18n.js / images/ を同梱必須**（場所: `app/src/main/assets/`）。

## ファイル一覧
| ファイル | 役割 | 備考 |
|---|---|---|
| `cutcalc.html` | 本体（UI＋ロジック＋i18nエンジン） | 単一運用。これだけで動くが、翻訳には i18n.js が必要 |
| `i18n.js` | **多言語辞書**（`window.I18N`） | cutcalc.html より**先に読み込む**。言語追加はこのファイルだけ編集 |
| `images/` | 使い方/解説の図（SVG） | sashigane.svg / usage-basic.svg など。**図中の文字は翻訳対象外（日本語のまま）** |
| `privacy.html` | プライバシーポリシー | Play提出用 |
| `figpreview-saved.html` | 断面図/底面図の確定版プレビュー（参考） | git管理外・作業用 |
| `cutcalc-pre-i18n.html` | 多言語化前のバックアップ | git管理外・作業用 |

## 多言語（i18n）の仕組み
- 辞書は `i18n.js` の `window.I18N = { ja:{…}, en:{…}, vi:{…}, zh:{…}, pt:{…}, fil:{…} }`。
- 対応言語: **日本語 / English / Tiếng Việt / 中文(簡体) / Português / Filipino**。
- エンジン（`cutcalc.html` 内）: `detectLang()`（保存値→ブラウザ言語→ja）、`t(key)`（未訳は ja にフォールバック）、`applyI18n()`（`data-i18n*` 属性と動的文字列を反映）、`setLang(l)`（`localStorage: cutcalc_lang` に保存）。
- HTML側: `data-i18n="キー"`（innerHTML）/ `data-i18n-ph`（placeholder）/ `data-i18n-title`（title）/ `data-i18n-aria`（aria-label）。
- 動的文字列（JS生成）: `t('キー')` を使用（ステータス、上部表示バー、記録一覧 等）。

### 言語を追加する手順
1. `i18n.js` の `window.I18N` に新ブロックを追加（例 `ko:{…}`）。**キー名は既存と同一**にする。
2. `cutcalc.html` ヘッダの `<select id="langSel">` に `<option value="ko">한국어</option>` を追加。
3. （アプリ配布する場合）更新した `i18n.js` を Android の `assets/` にもコピー。

### 翻訳範囲
- **対象**: 操作UI全般＋使い方/解説モーダルの本文。
- **対象外**: 図（SVG）中の文字、アプリ名「側溝カットガイド」。

## ビルド（Android）メモ
- `JAVA_HOME="C:\Program Files\Android\Android Studio\jbr"` で `.\gradlew.bat`。
- 署名キー: `C:\Users\ipconfig\Desktop\keystores\hactools`（PKCS12, alias `ucutguide`）。
- **assets を更新したら**（cutcalc.html / i18n.js / images/）リビルドして AAB を作成。

## 反映フロー（Web）
1. `cutcalc.html` / `i18n.js` を編集（作業フォルダ `EA\work\Cutcalc`）。
2. クローン `C:\tmp\sokkou_work` へコピー → `git add` → `commit` → `git push origin HEAD:workmain`（必要なら `:work` にも）。
3. スマホで `https://takedia.github.io/sokkou_cut/cutcalc.html` を再読込（Pages反映に約1分）。
