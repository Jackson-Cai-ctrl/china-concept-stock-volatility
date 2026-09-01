"""
基于混合数据源的2023年1月1日-2026年3月31日股票日线数据
所有股票统一切换为高稳定的 YFinance，宏观/行业使用 AKShare
"""

import os
import akshare as ak
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# 彻底禁用 requests 代理，防止 AKShare 宏观接口偶发报错
os.environ["http_proxy"] = ""
os.environ["https_proxy"] = ""
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""

# ==========================================
# 1. 配置参数
# ==========================================
START_DATE = '20230101'
END_DATE = '20260331'
YF_START = '2023-01-01'
YF_END = '2026-03-31'

REPRESENTATIVE_STOCKS = {
    # A股
    '600519': '贵州茅台',  
    '000858': '五粮液',    
    '000333': '美的集团',  
    '002415': '海康威视',  
    '300750': '宁德时代',  
    
    # 港股
    '00700': '腾讯控股',   
    '09988': '阿里巴巴',   
    '09618': '京东集团',   
    '09888': '百度集团',   
    '02020': '安踏体育',   
    '01810': '小米集团',   
    
    # 美股
    'BABA': '阿里巴巴',    
    'BIDU': '百度',        
    'JD': '京东',          
    'NIO': '蔚来',         
    'LI': '理想汽车',      
}

# ==========================================
# 2. 辅助函数
# ==========================================
def filter_time_range(df, start=START_DATE, end=END_DATE):
    if df.empty:
        return df
    
    date_columns = ['日期', 'date', 'Date', '时间', 'time', 'trade_date', 'datetime']
    for col in date_columns:
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col]).dt.tz_localize(None)
                mask = (df[col] >= pd.to_datetime(start)) & (df[col] <= pd.to_datetime(end))
                return df[mask]
            except:
                continue
    return df

def safe_fetch(label, func, *args, **kwargs):
    try:
        print(f"正在获取: {label}...")
        df = func(*args, **kwargs)
        if df is not None and not df.empty:
            print(f"  ✓ {label}: 成功获取 {len(df)} 条记录")
            return df
        else:
            print(f"  ⚠ {label}: 数据为空")
            return pd.DataFrame()
    except Exception as exc:
        print(f"  ✗ {label}: 请求失败 - {exc}")
        return pd.DataFrame()

def calculate_metrics(df, stock_name):
    if df.empty:
        return None
    
    metrics = {
        '股票名称': stock_name,
        '数据条数': len(df),
        '开始日期': df['日期'].min().strftime('%Y-%m-%d') if '日期' in df.columns else 'N/A',
        '结束日期': df['日期'].max().strftime('%Y-%m-%d') if '日期' in df.columns else 'N/A',
    }
    
    close_col = '收盘' if '收盘' in df.columns else 'Close' if 'Close' in df.columns else None
    if not close_col:
        return metrics
    
    if len(df) > 1:
        first_close = df[close_col].iloc[0]
        last_close = df[close_col].iloc[-1]
        price_change = ((last_close - first_close) / first_close) * 100
        metrics['价格变化率(%)'] = round(price_change, 2)
        
        if len(df) > 10:
            daily_returns = df[close_col].pct_change().dropna()
            annual_volatility = daily_returns.std() * np.sqrt(252) * 100
            metrics['年化波动率(%)'] = round(annual_volatility, 2)
    
    return metrics

# ==========================================
# 3. 主数据获取函数 (A股也切为 YFinance)
# ==========================================
def fetch_stock_daily_data():
    print("=" * 60)
    print("开始获取2023-01-01至2026-03-31股票日线数据")
    print("=" * 60)
    
    all_data = {}
    all_metrics = []
    
    for stock_code, stock_name in REPRESENTATIVE_STOCKS.items():
        print(f"\n处理股票: {stock_name} ({stock_code})")
        df = pd.DataFrame()
        
        try:
            if stock_code in ['BABA', 'BIDU', 'JD', 'NIO', 'LI']:
                # 美股
                yf_ticker = stock_code
                print(f"  调用 YFinance 获取美股数据 ({yf_ticker})...")
                
            elif len(stock_code) == 5 and stock_code.startswith('0'):
                # 港股 (加 .HK)
                yf_ticker = f"{stock_code[1:]}.HK"
                print(f"  调用 YFinance 获取港股数据 ({yf_ticker})...")
                
            else:
                # 【新增】A股使用 YFinance (沪市加 .SS，深市加 .SZ)
                if stock_code.startswith('6'):
                    yf_ticker = f"{stock_code}.SS"
                else:
                    yf_ticker = f"{stock_code}.SZ"
                print(f"  调用 YFinance 获取A股数据 ({yf_ticker})...")
            
            # 统一执行 YFinance 下载
            df = yf.download(yf_ticker, start=YF_START, end=YF_END, progress=False)
            
            if not df.empty:
                # 清洗列名
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.droplevel(1)
                df = df.reset_index()
                df.rename(columns={'Date': '日期', 'Open': '开盘', 'Close': '收盘', 'High': '最高', 'Low': '最低', 'Volume': '成交量'}, inplace=True)
                
        except Exception as e:
            print(f"  ⚠ 获取异常: {e}")
            
        df = filter_time_range(df)
        
        if not df.empty:
            all_data[f"{stock_name}_{stock_code}"] = df
            metrics = calculate_metrics(df, stock_name)
            if metrics:
                all_metrics.append(metrics)
            
            csv_filename = f"stock_{stock_code}_{stock_name}_2023_2026.csv"
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"  ✓ 数据已保存: {csv_filename} (共 {len(df)} 条)")
        else:
            print(f"  ⚠ 未获取到有效数据")
            
    return all_data, all_metrics

def fetch_macro_data():
    print("\n" + "=" * 60)
    print("获取宏观经济数据")
    print("=" * 60)
    
    macro_data = {}
    macro_functions = {
        '中国CPI': ak.macro_china_cpi,
        '中国GDP': ak.macro_china_gdp,
        '中国PMI': ak.macro_china_pmi,
        '中国货币供应量': ak.macro_china_money_supply,
        '中国股市市值': ak.macro_china_stock_market_cap,
        '中国LPR': ak.macro_china_lpr,
    }
    
    for name, func in macro_functions.items():
        df = safe_fetch(name, func)
        if not df.empty:
            df_filtered = filter_time_range(df)
            if not df_filtered.empty:
                macro_data[name] = df_filtered
                csv_filename = f"macro_{name}_2023_2026.csv"
                df_filtered.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                
    return macro_data

def fetch_industry_data():
    print("\n" + "=" * 60)
    print("获取行业和概念板块数据")
    print("=" * 60)
    
    industry_data = {}
    concept_df = safe_fetch('概念板块列表', ak.stock_board_concept_name_em)
    
    if not concept_df.empty:
        industry_data['概念板块列表'] = concept_df
        concept_df.to_csv('concept_boards_2023_2026.csv', index=False, encoding='utf-8-sig')
        
        for i in range(min(3, len(concept_df))):
            # 【修复】准确抓取板块名称列，防止获取到数字排名
            if '板块名称' in concept_df.columns:
                concept_name = concept_df.iloc[i]['板块名称']
            elif '概念名称' in concept_df.columns:
                concept_name = concept_df.iloc[i]['概念名称']
            else:
                concept_name = concept_df.iloc[i, 1] # 通常第二列是名称
            
            # 成分股
            cons_df = safe_fetch(f'{concept_name}成分股', ak.stock_board_concept_cons_em, symbol=concept_name)
            if not cons_df.empty:
                industry_data[f'{concept_name}_成分股'] = cons_df
                cons_df.to_csv(f'concept_{concept_name}_constituents.csv', index=False, encoding='utf-8-sig')
                
    return industry_data

# ==========================================
# 4. 数据分析和可视化
# ==========================================
def analyze_and_visualize(stock_metrics, stock_data):
    if not stock_metrics:
        print("没有足够的指标数据进行可视化")
        return
    
    metrics_df = pd.DataFrame(stock_metrics)
    metrics_df.to_csv('stock_metrics_summary_2023_2026.csv', index=False, encoding='utf-8-sig')
    print("\n指标汇总:")
    print(metrics_df.to_string())
    
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    
    if '价格变化率(%)' in metrics_df.columns:
        plt.figure(figsize=(14, 8))
        metrics_sorted = metrics_df.sort_values('价格变化率(%)', ascending=False)
        bars = plt.bar(metrics_sorted['股票名称'], metrics_sorted['价格变化率(%)'])
        
        for bar in bars:
            bar.set_color('green' if bar.get_height() >= 0 else 'red')
        
        plt.title('代表性股票价格变化率 (2023-01-01 至 2026-03-31)', fontsize=16)
        plt.ylabel('价格变化率 (%)', fontsize=14)
        plt.xticks(rotation=45, ha='right')
        plt.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        plt.tight_layout()
        plt.savefig('stock_price_change_2023_2026.png', dpi=300, bbox_inches='tight')
    
    if '年化波动率(%)' in metrics_df.columns:
        plt.figure(figsize=(14, 8))
        metrics_sorted = metrics_df.sort_values('年化波动率(%)', ascending=False)
        plt.bar(metrics_sorted['股票名称'], metrics_sorted['年化波动率(%)'], color='steelblue')
        plt.title('代表性股票年化波动率 (2023-01-01 至 2026-03-31)', fontsize=16)
        plt.ylabel('年化波动率 (%)', fontsize=14)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig('stock_volatility_2023_2026.png', dpi=300, bbox_inches='tight')
    
    top_stocks = list(stock_data.keys())[:5]
    if top_stocks:
        plt.figure(figsize=(14, 8))
        for stock_key in top_stocks:
            df = stock_data[stock_key]
            if not df.empty and '日期' in df.columns and '收盘' in df.columns:
                normalized_price = (df['收盘'] / df['收盘'].iloc[0]) * 100
                plt.plot(df['日期'], normalized_price, label=stock_key.split('_')[0], linewidth=2)
        
        plt.title('代表性股票价格走势 (标准化, 2023-01-01 至 2026-03-31)', fontsize=16)
        plt.ylabel('标准化价格 (起始日=100)', fontsize=14)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('stock_price_trends_2023_2026.png', dpi=300, bbox_inches='tight')

# ==========================================
# 5. 主函数
# ==========================================
def main():
    print("=" * 60)
    print("基于混合数据源的2023-2026年股票数据收集与分析")
    print("=" * 60)
    
    try:
        stock_data, stock_metrics = fetch_stock_daily_data()
        macro_data = fetch_macro_data()
        industry_data = fetch_industry_data()
        
        if stock_metrics:
            analyze_and_visualize(stock_metrics, stock_data)
        
        print("\n" + "=" * 60)
        total_stocks = len(REPRESENTATIVE_STOCKS)
        successful_stocks = len([m for m in stock_metrics if m.get('数据条数', 0) > 0])
        print(f"数据收集统计: 计划 {total_stocks} 只，成功 {successful_stocks} 只，成功率 {successful_stocks/total_stocks*100:.1f}%")
        print("数据收集和分析已全部完成!")
        
    except Exception as e:
        print(f"\n程序执行出错: {e}")

if __name__ == "__main__":
    main()