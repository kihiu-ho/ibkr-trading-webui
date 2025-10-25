-- Seed data for prompt_templates table
-- These are the default prompts extracted from the n8n workflow
-- Date: 2025-10-25

-- Clear existing prompt templates (optional, for development)
-- DELETE FROM prompt_templates WHERE created_by = 'system';

-- 1. Daily Chart Analysis Prompt (Chinese)
INSERT INTO prompt_templates (
    name, 
    description, 
    prompt_text, 
    template_version,
    template_type, 
    language, 
    strategy_id, 
    is_active, 
    is_default,
    created_by,
    tags,
    notes
) VALUES (
    'Daily Chart Technical Analysis (Traditional Chinese)',
    '日線技術分析提示詞 - 包含SuperTrend、移動平均線、MACD、RSI、ATR、布林帶及成交量分析',
    'Analysis Date: {{ now.strftime("%Y-%m-%d %H:%M:%S") }}

# 以下是日線分析結果

## 1. 核心價格分析
- 目前價格與趨勢概述
- 關鍵支撐/阻力位
- 重要K線形態與價格結構
- 圖表時間範圍：日線圖(主要)與週線圖(確認)

## 2. 趨勢指標分析
A. SuperTrend (10,3)：
   - 目前狀態：[上升趨勢/下降趨勢]
   - 信號顏色：[綠色/紅色]
   - 與價格的相對位置與最近變化

B. 移動平均線系統：
   - 20日SMA：短期趨勢方向
   - 50日SMA：中期趨勢方向
   - 200日SMA：長期趨勢方向
   - 黃金/死亡交叉情況
   - 價格與均線的關係(支撐/阻力)

## 3. 確認指標分析
A. 動能確認：
   - MACD (12,26,9)狀態與信號
   - RSI (14)水平與方向[超買/超賣/中性]

B. 波動性分析：
   - ATR (14)數值與趨勢{% if atr %}，目前ATR: {{ atr|round(2) }}{% endif %}
   - 布林帶(20,2)寬度與價格位置

C. 成交量分析：
   - 目前成交量vs.20日平均
   - 成交量趨勢特徵
   - OBV走勢與價格確認

## 4. 信號確認系統(3/4規則)
以下信號中，至少滿足3項才確認交易方向：
- SuperTrend信號方向[看漲/看跌]
- 價格與20日SMA關係[上方/下方]
- MACD信號線交叉[買入/賣出]
- RSI相對位置[>50看漲/<50看跌]

## 5. 交易建議
- 綜合趨勢判斷：[強烈看漲/看漲/中性/看跌/強烈看跌]
- 交易信號：[進場/持有/出場]

A. 如果看漲(多頭):
   - 進場區間：[價格區間]{% if current_price %} (參考價格: {{ current_price|round(2) }}){% endif %}
   - 止損位：入場價 - (2 × ATR)，約[具體數值]
   
   - 獲利目標：[高於目前價格的目標]
   - 目標價依據：
     * 第一目標(保守)：[數值] - 基於[支撐阻力/圖表形態/指標水平]
     * 第二目標(進取)：[數值] - 基於[支撐阻力/圖表形態/指標水平]
   
   - R倍數計算：(目標價 - 入場價) ÷ (入場價 - 止損位) = ?R

B. 如果看跌(空頭):
   - 進場區間：[價格區間]{% if current_price %} (參考價格: {{ current_price|round(2) }}){% endif %}
   - 止損位：入場價 + (2 × ATR)，約[具體數值]
   
   - 獲利目標：[低於目前價格的目標]
   - 目標價依據：
     * 第一目標(保守)：[數值] - 基於[支撐阻力/圖表形態/指標水平]
     * 第二目標(進取)：[數值] - 基於[支撐阻力/圖表形態/指標水平]
   
   - R倍數計算：(入場價 - 目標價) ÷ (止損位 - 入場價) = ?R

- 建議倉位大小：[%，基於固定風險管理]

## 6. 風險評估
- 主要技術風險
- 關鍵反轉價格
- 潛在信號失敗情境
- 週線圖確認情況

請提供綜合判斷並清晰說明理由，重點解釋關鍵指標之間的相互確認/矛盾情況。只有當多項指標同時確認時才給出明確入場建議。分析目標價時必須說明技術依據，如支撐阻力位、圖表形態測量、斐波那契水平、布林帶目標、均線位置、量能目標或波動幅度投射等。

## 目標價設定參考依據
分析目標價時，請從以下技術因素中選擇最適合的依據：

1. 前期支撐/阻力位：歷史高低點、交易密集區
2. 圖表形態投射：頭肩頂/底、三角形/旗形/楔形等形態測量目標
3. 斐波那契水平：延伸(127.2%, 161.8%)或回調(38.2%, 50%, 61.8%)
4. 布林帶目標：布林帶上/下軌或寬度投射
5. 移動平均線目標：重要均線位置或交叉點
6. 量能目標：成交量分佈峰值、成交量力場高低點
7. 波動幅度投射：基於ATR的波動範圍(如3倍ATR)',
    1,
    'analysis',
    'zh',
    NULL,  -- Global default
    TRUE,
    TRUE,  -- Set as default
    'system',
    ARRAY['technical-analysis', 'daily', 'chinese', 'supertrend', 'ma', 'rsi', 'macd'],
    'Extracted from n8n workflow: Analyze Daily Chart node'
) ON CONFLICT DO NOTHING;

-- 2. Weekly Chart Analysis Prompt (Chinese)
INSERT INTO prompt_templates (
    name, 
    description, 
    prompt_text, 
    template_version,
    template_type, 
    language, 
    strategy_id, 
    is_active, 
    is_default,
    created_by,
    tags,
    notes
) VALUES (
    'Weekly Chart Trend Confirmation (Traditional Chinese)',
    '週線趨勢確認提示詞 - 提供中期趨勢評估與日線信號確認',
    'Analysis Date: {{ now.strftime("%Y-%m-%d %H:%M:%S") }}

# 以下是週線分析結果

## 1. 中期趨勢評估
- 近12個月週線趨勢方向與強度[上升/盤整/下降]
- 主要趨勢線與通道分析
- 週線趨勢階段判定[初期/中期/後期]
- SuperTrend週線指標狀態

## 2. 關鍵價位分析
- 12個月內主要支撐位[價格區間與重要性]
- 12個月內主要阻力位[價格區間與重要性]
- 目前價格相對區間位置評估{% if current_price %} (目前價格: {{ current_price|round(2) }}){% endif %}
- 中期價值區間判定

## 3. 週線指標分析
- 週線RSI(14)：中期超買/超賣狀態
- 週線MACD(12,26,9)：中期動能
- 週線平均線系統：10週/20週/50週均線關係
- 週線布林帶(20,2)位置與寬度

## 4. 中期價格形態
- 近期形成的週線圖形態
- 週線突破/回踩情況
- 近期的反轉信號
- 中期趨勢強度評估

## 5. 週線成交量特徵
- 週線成交量趨勢
- 重要週線量價關係
- 週線OBV趨勢
- 異常成交量週分析

## 6. 日線與週線協同分析
- 日線與週線趨勢一致性判斷
- 趨勢衝突分析(如有)
- 週線如何支持或反對日線信號
- 日線信號在週線背景下的可靠性

## 7. 中期展望(30-180天)
- 未來1-6個月趨勢預期
- 關鍵轉折點識別
- 中期持有的主要風險
- 最值得關注的週線預警信號

請提供週線圖的中期趨勢分析，特別強調週線和日線信號的一致性或差異性，為30-180天的交易決策提供參考。分析應關注形態的完整性、趨勢的強度以及支撐阻力位的可靠性。',
    1,
    'analysis',
    'zh',
    NULL,  -- Global default
    TRUE,
    FALSE,  -- Not default (daily is default for analysis type)
    'system',
    ARRAY['technical-analysis', 'weekly', 'chinese', 'trend-confirmation'],
    'Extracted from n8n workflow: Analyze Weekly Chart node'
) ON CONFLICT DO NOTHING;

-- 3. Consolidation/Final Report Prompt (Chinese)
INSERT INTO prompt_templates (
    name, 
    description, 
    prompt_text, 
    template_version,
    template_type, 
    language, 
    strategy_id, 
    is_active, 
    is_default,
    created_by,
    tags,
    notes
) VALUES (
    'Multi-Timeframe Analysis Consolidation (Traditional Chinese)',
    '多時間框架整合分析 - 結合日線與週線分析生成最終交易建議',
    'Analysis Date: {{ now.strftime("%Y-%m-%d %H:%M:%S") }}

## 日線分析摘要
{% if analysis_daily %}
{{ analysis_daily }}
{% else %}
[日線分析結果將在此處顯示]
{% endif %}

## 週線分析摘要
{% if analysis_weekly %}
{{ analysis_weekly }}
{% else %}
[週線分析結果將在此處顯示]
{% endif %}

# 整合技術分析報告

## 1. 價格與趨勢概述
- 目前價格與整體趨勢狀態{% if current_price %} (目前價格: {{ current_price|round(2) }}){% endif %}
- 日線主要趨勢方向與強度
- 週線趨勢確認情況
- 價格相對於關鍵支撐阻力位置
- 跨時間框架趨勢一致性評估

## 2. 技術分析摘要
- SuperTrend信號在日線與週線的狀態
- 移動平均線系統跨時間框架分析
- 動能指標(MACD、RSI)關鍵讀數與確認
- 波動性指標(ATR、布林帶)重要數值{% if atr %} (ATR: {{ atr|round(2) }}){% endif %}
- 成交量分析與跨時間框架確認
- 關鍵技術形態與影響

## 3. 多時間框架信號確認系統
- 日線3/4規則信號結果
- 週線對日線信號的支持/反對程度
- 跨時間框架確認強度[強/中/弱]
- 任何顯著的時間框架衝突與解決方案
- 最終確認信號判定[確認/部分確認/未確認]

## 4. 詳細交易建議
- 綜合趨勢判斷：[強烈看漲/看漲/中性/看跌/強烈看跌]
- 交易信號：[進場/持有/出場]

A. 如果看漲(多頭):
   - 建議進場區間：[具體價格範圍]
   - 止損位：[具體價格] (基於日線ATR，週線確認)
   - 目標價格：
     * 第一目標(保守)：[具體價格] - [技術依據]
     * 第二目標(進取)：[具體價格] - [技術依據]
   - R倍數：[具體數值]計算
   - 預期獲利百分比：[具體數值]%

B. 如果看跌(空頭):
   - 建議進場區間：[具體價格範圍]
   - 止損位：[具體價格] (基於日線ATR，週線確認)
   - 目標價格：
     * 第一目標(保守)：[具體價格] - [技術依據]
     * 第二目標(進取)：[具體價格] - [技術依據]
   - R倍數：[具體數值]計算
   - 預期獲利百分比：[具體數值]%

- 建議倉位大小：[%]
- 交易時機與執行策略
- 階段性目標與調整點

## 5. 風險評估
- 主要技術風險因素
- 週線圖識別的額外風險考量
- 關鍵反轉價格與警戒點
- 潛在信號失敗情境
- 跨時間框架的風險監控重點
- 如何管理及降低已識別風險

## 6. 結論
- 最終交易建議摘要
- 主要理由與技術依據
- 關鍵監控指標與時間點
- 交易計劃時效性與後續更新建議

請提供詳細而全面的整合分析，確保所有交易參數清晰明確，並著重說明關鍵技術依據。報告應突出日線分析為主導，同時展示週線趨勢如何確認或調整主要交易觀點。',
    1,
    'consolidation',
    'zh',
    NULL,  -- Global default
    TRUE,
    TRUE,  -- Set as default for consolidation type
    'system',
    ARRAY['consolidation', 'multi-timeframe', 'chinese', 'final-report'],
    'Extracted from n8n workflow: Consolidate Daily&Weekly node'
) ON CONFLICT DO NOTHING;

-- 4. System Message Prompts (English and Chinese)
INSERT INTO prompt_templates (
    name, 
    description, 
    prompt_text, 
    template_version,
    template_type, 
    language, 
    strategy_id, 
    is_active, 
    is_default,
    created_by,
    tags,
    notes
) VALUES (
    'System Message - Daily Analysis (Chinese)',
    '日線分析系統訊息 - 設定分析師角色與回覆規則',
    'You are a professional technical analyst specialized in medium-term trading (30-180 days holding period) based on Daily candle chart of {{ symbol }}{% if exchange %} in exchange {{ exchange }}{% endif %}. Please analyze using the following framework.

使用通順的繁體中文回覆我

## 字詞翻譯轉換
- 回調 -> 回檔
- 股利 -> 股息
- 派息 -> 配息
- 視頻 -> 影片
- 音頻 -> 語音
- 增長 -> 成長
- 智能 -> 智慧
- 編程 -> 寫程式',
    1,
    'system_message',
    'zh',
    NULL,
    TRUE,
    TRUE,
    'system',
    ARRAY['system-message', 'daily', 'chinese'],
    'System message for daily chart analysis'
) ON CONFLICT DO NOTHING;

INSERT INTO prompt_templates (
    name, 
    description, 
    prompt_text, 
    template_version,
    template_type, 
    language, 
    strategy_id, 
    is_active, 
    is_default,
    created_by,
    tags,
    notes
) VALUES (
    'System Message - Weekly Analysis (Chinese)',
    '週線分析系統訊息 - 設定分析師角色與回覆規則',
    'You are a professional technical analyst specializing in weekly chart analysis. Please analyze the weekly chart of {{ symbol }}{% if exchange %} in exchange {{ exchange }}{% endif %} for the past 12 months, focusing on trend confirmation to support medium-term (30-180 days) trading decisions.

使用通順的繁體中文回覆我

## 字詞翻譯轉換
- 回調 -> 回檔
- 股利 -> 股息
- 派息 -> 配息
- 視頻 -> 影片
- 音頻 -> 語音
- 增長 -> 成長
- 智能 -> 智慧
- 編程 -> 寫程式',
    1,
    'system_message',
    'zh',
    NULL,
    TRUE,
    FALSE,
    'system',
    ARRAY['system-message', 'weekly', 'chinese'],
    'System message for weekly chart analysis'
) ON CONFLICT DO NOTHING;

INSERT INTO prompt_templates (
    name, 
    description, 
    prompt_text, 
    template_version,
    template_type, 
    language, 
    strategy_id, 
    is_active, 
    is_default,
    created_by,
    tags,
    notes
) VALUES (
    'System Message - Consolidation (Chinese)',
    '整合分析系統訊息 - 設定分析師角色與回覆規則',
    'You are a professional technical analyst creating a comprehensive trading recommendation based primarily on daily chart analysis, with weekly chart serving as trend confirmation. Please synthesize a detailed final analysis report for {{ symbol }} focused on medium-term (30-180 days) trading opportunities.
不需要額外輸出週線趨勢確認分析，週線分析僅作為趨勢確認使用。

使用通順的繁體中文回覆我。

## 字詞翻譯轉換
- 回調 -> 回檔
- 股利 -> 股息
- 派息 -> 配息
- 增長 -> 成長
- 視頻 -> 影片
- 音頻 -> 語音
- 智能 -> 智慧
- 邊程 -> 寫程式
- 創建 -> 建立
- 編程 -> 程式開發',
    1,
    'system_message',
    'zh',
    NULL,
    TRUE,
    FALSE,
    'system',
    ARRAY['system-message', 'consolidation', 'chinese'],
    'System message for consolidation analysis'
) ON CONFLICT DO NOTHING;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'Prompt templates seeded successfully. Total: 6 templates (3 main analysis + 3 system messages)';
END $$;

