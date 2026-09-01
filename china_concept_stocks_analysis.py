"""
中概股波动成因深度分析
基于2023-2026年数据，进行多维度分析
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')
import os

# ==========================================
# 1. 配置和设置
# ==========================================
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 定义股票分类
STOCK_CATEGORIES = {
    '互联网平台': ['00700', '09988', '09618', '09888', 'BABA', 'BIDU', 'JD', 'TCEHY'],
    '新能源汽车': ['NIO', 'LI', '09866', '09868', '02015'],
    '消费电子': ['01810'],
    '消费龙头': ['600519', '000858', '02020'],
    '家电龙头': ['000333'],
    '科技龙头': ['002415'],
    '新能源龙头': ['300750']
}

# ==========================================
# 2. 数据加载和预处理
# ==========================================
def load_all_stock_data():
    """加载所有股票数据"""
    stock_files = [f for f in os.listdir('.') if f.startswith('stock_') and f.endswith('_2023_2026.csv')]
    
    all_stocks_data = {}
    stock_info = {}
    
    for file in stock_files:
        try:
            # 从文件名提取股票信息
            parts = file.replace('stock_', '').replace('_2023_2026.csv', '').split('_')
            if len(parts) >= 2:
                stock_code = parts[0]
                stock_name = parts[1]
                
                # 加载数据
                df = pd.read_csv(file, encoding='utf-8-sig')
                
                # 标准化列名
                column_mapping = {
                    '日期': 'date',
                    'date': 'date',
                    '收盘': 'close',
                    'close': 'close',
                    '开盘': 'open',
                    'open': 'open',
                    '最高': 'high',
                    'high': 'high',
                    '最低': 'low',
                    'low': 'low',
                    '成交量': 'volume',
                    'volume': 'volume',
                    '成交额': 'amount',
                    'amount': 'amount'
                }
                
                for old_col, new_col in column_mapping.items():
                    if old_col in df.columns:
                        df = df.rename(columns={old_col: new_col})
                
                # 确保日期格式
                df['date'] = pd.to_datetime(df['date'])
                
                # 计算日收益率
                df['daily_return'] = df['close'].pct_change()
                
                # 计算滚动波动率（20日）
                df['volatility_20d'] = df['daily_return'].rolling(window=20).std() * np.sqrt(252) * 100
                
                # 计算滚动最大回撤（60日）
                df['cumulative_return'] = (1 + df['daily_return']).cumprod()
                df['rolling_max'] = df['cumulative_return'].rolling(window=60, min_periods=1).max()
                df['drawdown'] = (df['cumulative_return'] - df['rolling_max']) / df['rolling_max'] * 100
                
                all_stocks_data[stock_code] = df
                stock_info[stock_code] = {
                    'name': stock_name,
                    'category': get_stock_category(stock_code)
                }
                
                print(f"✓ 加载: {stock_name} ({stock_code}), {len(df)} 条记录")
                
        except Exception as e:
            print(f"✗ 加载 {file} 失败: {e}")
    
    return all_stocks_data, stock_info

def get_stock_category(stock_code):
    """获取股票分类"""
    for category, codes in STOCK_CATEGORIES.items():
        if stock_code in codes:
            return category
    return '其他'

def load_macro_data():
    """加载宏观经济数据"""
    macro_files = [f for f in os.listdir('.') if f.startswith('macro_') and f.endswith('_2023_2026.csv')]
    
    macro_data = {}
    
    for file in macro_files:
        try:
            name = file.replace('macro_', '').replace('_2023_2026.csv', '')
            df = pd.read_csv(file, encoding='utf-8-sig')
            macro_data[name] = df
            print(f"✓ 加载宏观经济: {name}, {len(df)} 条记录")
        except Exception as e:
            print(f"✗ 加载 {file} 失败: {e}")
    
    return macro_data

# ==========================================
# 3. 缺失值分析和数据质量检查
# ==========================================
def analyze_missing_values(all_stocks_data):
    """分析缺失值"""
    print("\n" + "=" * 60)
    print("缺失值分析")
    print("=" * 60)
    
    missing_summary = []
    
    for stock_code, df in all_stocks_data.items():
        total_rows = len(df)
        missing_close = df['close'].isnull().sum()
        missing_return = df['daily_return'].isnull().sum()
        
        missing_summary.append({
            '股票代码': stock_code,
            '总记录数': total_rows,
            '收盘价缺失数': missing_close,
            '收盘价缺失率(%)': round(missing_close/total_rows*100, 2),
            '收益率缺失数': missing_return,
            '收益率缺失率(%)': round(missing_return/total_rows*100, 2)
        })
    
    missing_df = pd.DataFrame(missing_summary)
    print(missing_df.to_string())
    
    # 检查数据完整性
    print(f"\n数据完整性检查:")
    print(f"- 总股票数量: {len(all_stocks_data)}")
    print(f"- 平均记录数: {missing_df['总记录数'].mean():.0f}")
    print(f"- 最大缺失率: {missing_df['收盘价缺失率(%)'].max():.2f}%")
    print(f"- 最小缺失率: {missing_df['收盘价缺失率(%)'].min():.2f}%")
    
    return missing_df

# ==========================================
# 4. 多维度波动分析
# ==========================================
def analyze_volatility_by_year(all_stocks_data, stock_info):
    """按年份分析波动性"""
    print("\n" + "=" * 60)
    print("按年份波动分析 (2023-2026)")
    print("=" * 60)
    
    yearly_analysis = []
    
    for stock_code, df in all_stocks_data.items():
        stock_name = stock_info[stock_code]['name']
        category = stock_info[stock_code]['category']
        
        # 按年份分组
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        
        for year in [2023, 2024, 2025, 2026]:
            year_data = df[df['year'] == year]
            
            if len(year_data) > 20:  # 至少有20个交易日
                # 计算年度指标
                if len(year_data) > 1:
                    first_close = year_data['close'].iloc[0]
                    last_close = year_data['close'].iloc[-1]
                    annual_return = ((last_close - first_close) / first_close) * 100
                else:
                    annual_return = np.nan
                
                annual_volatility = year_data['daily_return'].std() * np.sqrt(252) * 100
                
                # 计算最大回撤
                if len(year_data) > 10:
                    cumulative = (1 + year_data['daily_return']).cumprod()
                    rolling_max = cumulative.expanding().max()
                    drawdown = (cumulative - rolling_max) / rolling_max
                    max_drawdown = drawdown.min() * 100
                else:
                    max_drawdown = np.nan
                
                yearly_analysis.append({
                    '股票代码': stock_code,
                    '股票名称': stock_name,
                    '行业分类': category,
                    '年份': year,
                    '年度收益率(%)': round(annual_return, 2),
                    '年化波动率(%)': round(annual_volatility, 2),
                    '最大回撤(%)': round(max_drawdown, 2) if not np.isnan(max_drawdown) else np.nan,
                    '交易天数': len(year_data)
                })
    
    yearly_df = pd.DataFrame(yearly_analysis)
    
    # 保存年度分析结果
    yearly_df.to_csv('yearly_volatility_analysis_2023_2026.csv', index=False, encoding='utf-8-sig')
    
    # 打印汇总统计
    print("\n年度波动性汇总:")
    yearly_pivot = yearly_df.pivot_table(
        index=['行业分类', '股票名称'],
        columns='年份',
        values='年化波动率(%)',
        aggfunc='mean'
    )
    print(yearly_pivot.to_string())
    
    return yearly_df

def analyze_volatility_causes(yearly_df, macro_data):
    """分析波动成因"""
    print("\n" + "=" * 60)
    print("波动成因分析")
    print("=" * 60)
    
    # 按年份和行业分析
    yearly_summary = yearly_df.groupby(['年份', '行业分类']).agg({
        '年度收益率(%)': 'mean',
        '年化波动率(%)': 'mean',
        '最大回撤(%)': 'mean'
    }).round(2)
    
    print("按年份和行业的波动性:")
    print(yearly_summary.to_string())
    
    # 分析每年的主要波动特征
    print("\n各年份波动特征分析:")
    
    for year in [2023, 2024, 2025, 2026]:
        year_data = yearly_df[yearly_df['年份'] == year]
        
        if len(year_data) > 0:
            avg_return = year_data['年度收益率(%)'].mean()
            avg_volatility = year_data['年化波动率(%)'].mean()
            worst_industry = year_data.groupby('行业分类')['年度收益率(%)'].mean().idxmin()
            best_industry = year_data.groupby('行业分类')['年度收益率(%)'].mean().idxmax()
            
            print(f"\n{year}年:")
            print(f"  - 平均收益率: {avg_return:.2f}%")
            print(f"  - 平均波动率: {avg_volatility:.2f}%")
            print(f"  - 表现最佳行业: {best_industry}")
            print(f"  - 表现最差行业: {worst_industry}")
            
            # 分析极端波动股票
            high_vol_stocks = year_data.nlargest(3, '年化波动率(%)')
            low_vol_stocks = year_data.nsmallest(3, '年化波动率(%)')
            
            print(f"  - 高波动股票: {', '.join([f'{row["股票名称"]}({row["年化波动率(%)"]}%)' for _, row in high_vol_stocks.iterrows()])}")
            print(f"  - 低波动股票: {', '.join([f'{row["股票名称"]}({row["年化波动率(%)"]}%)' for _, row in low_vol_stocks.iterrows()])}")

def analyze_industry_differences(yearly_df):
    """行业差异分析"""
    print("\n" + "=" * 60)
    print("行业差异分析")
    print("=" * 60)
    
    # 计算各行业整体表现
    industry_performance = yearly_df.groupby('行业分类').agg({
        '年度收益率(%)': ['mean', 'std', 'min', 'max'],
        '年化波动率(%)': 'mean',
        '最大回撤(%)': 'mean'
    }).round(2)
    
    print("各行业表现对比:")
    print(industry_performance.to_string())
    
    # 行业相关性分析
    industry_returns = yearly_df.pivot_table(
        index='年份',
        columns='行业分类',
        values='年度收益率(%)',
        aggfunc='mean'
    )
    
    industry_correlation = industry_returns.corr()
    
    print("\n行业收益率相关性矩阵:")
    print(industry_correlation.round(2).to_string())
    
    # 识别高相关性和低相关性行业对
    print("\n行业相关性分析:")
    for i in range(len(industry_correlation.columns)):
        for j in range(i+1, len(industry_correlation.columns)):
            corr_value = industry_correlation.iloc[i, j]
            if abs(corr_value) > 0.7:
                print(f"  高相关性: {industry_correlation.columns[i]} & {industry_correlation.columns[j]}: {corr_value:.2f}")
            elif abs(corr_value) < 0.3:
                print(f"  低相关性: {industry_correlation.columns[i]} & {industry_correlation.columns[j]}: {corr_value:.2f}")
    
    return industry_performance, industry_correlation

# ==========================================
# 5. 可视化分析
# ==========================================
def create_visualizations(yearly_df, industry_performance):
    """创建可视化图表"""
    print("\n" + "=" * 60)
    print("生成可视化图表")
    print("=" * 60)
    
    # 1. 各行业年度收益率热力图
    plt.figure(figsize=(12, 8))
    industry_year_heatmap = yearly_df.pivot_table(
        index='行业分类',
        columns='年份',
        values='年度收益率(%)',
        aggfunc='mean'
    )
    
    sns.heatmap(industry_year_heatmap, annot=True, fmt='.1f', cmap='RdYlGn', 
                center=0, linewidths=0.5, cbar_kws={'label': '收益率(%)'})
    plt.title('各行业年度收益率热力图 (2023-2026)', fontsize=16)
    plt.tight_layout()
    plt.savefig('industry_year_return_heatmap.png', dpi=300, bbox_inches='tight')
    print("✓ 生成: industry_year_return_heatmap.png")
    
    # 2. 各行业波动率对比
    plt.figure(figsize=(14, 8))
    industry_volatility = yearly_df.groupby('行业分类')['年化波动率(%)'].mean().sort_values(ascending=False)
    
    bars = plt.bar(industry_volatility.index, industry_volatility.values)
    plt.title('各行业平均年化波动率对比 (2023-2026)', fontsize=16)
    plt.ylabel('年化波动率(%)', fontsize=14)
    plt.xlabel('行业分类', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    
    # 添加数值标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{height:.1f}%', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('industry_volatility_comparison.png', dpi=300, bbox_inches='tight')
    print("✓ 生成: industry_volatility_comparison.png")
    
    # 3. 年度波动趋势图
    plt.figure(figsize=(14, 8))
    yearly_vol_trend = yearly_df.groupby('年份')['年化波动率(%)'].mean()
    
    plt.plot(yearly_vol_trend.index.astype(str), yearly_vol_trend.values, 
             marker='o', linewidth=2, markersize=8)
    plt.title('年度平均波动率趋势 (2023-2026)', fontsize=16)
    plt.ylabel('平均年化波动率(%)', fontsize=14)
    plt.xlabel('年份', fontsize=14)
    plt.grid(True, alpha=0.3)
    
    # 添加数值标签
    for x, y in zip(yearly_vol_trend.index, yearly_vol_trend.values):
        plt.text(x, y + 0.5, f'{y:.1f}%', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('yearly_volatility_trend.png', dpi=300, bbox_inches='tight')
    print("✓ 生成: yearly_volatility_trend.png")
    
    # 4. 行业收益率分布箱线图
    plt.figure(figsize=(14, 8))
    yearly_df_sorted = yearly_df.copy()
    yearly_df_sorted['行业分类'] = pd.Categorical(yearly_df_sorted['行业分类'], 
                                                categories=industry_volatility.index.tolist())
    
    sns.boxplot(data=yearly_df_sorted, x='行业分类', y='年度收益率(%)')
    plt.title('各行业收益率分布箱线图 (2023-2026)', fontsize=16)
    plt.ylabel('年度收益率(%)', fontsize=14)
    plt.xlabel('行业分类', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.axhline(y=0, color='red', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig('industry_return_distribution.png', dpi=300, bbox_inches='tight')
    print("✓ 生成: industry_return_distribution.png")

# ==========================================
# 6. 展望和建议
# ==========================================
def generate_recommendations(yearly_df, industry_performance, industry_correlation):
    """生成展望和建议"""
    print("\n" + "=" * 60)
    print("展望和建议")
    print("=" * 60)
    
    recommendations = []
    
    # 1. 基于历史表现的建议
    print("\n1. 基于历史表现的投资建议:")
    
    # 找出表现稳定且收益良好的行业
    stable_industries = []
    for industry in industry_performance.index:
        avg_return = industry_performance.loc[industry, ('年度收益率(%)', 'mean')]
        avg_volatility = industry_performance.loc[industry, ('年化波动率(%)', 'mean')]
        
        if avg_return > 0 and avg_volatility < 30:
            stable_industries.append((industry, avg_return, avg_volatility))
            print(f"   - {industry}: 平均收益率 {avg_return:.1f}%, 波动率 {avg_volatility:.1f}% (稳健)")
    
    # 找出高增长但高波动的行业
    growth_industries = []
    for industry in industry_performance.index:
        avg_return = industry_performance.loc[industry, ('年度收益率(%)', 'mean')]
        avg_volatility = industry_performance.loc[industry, ('年化波动率(%)', 'mean')]
        
        if avg_return > 10 and avg_volatility > 35:
            growth_industries.append((industry, avg_return, avg_volatility))
            print(f"   - {industry}: 平均收益率 {avg_return:.1f}%, 波动率 {avg_volatility:.1f}% (高增长高波动)")
    
    # 2. 基于相关性的资产配置建议
    print("\n2. 基于相关性的资产配置建议:")
    
    # 寻找低相关性行业对进行分散投资
    low_corr_pairs = []
    for i in range(len(industry_correlation.columns)):
        for j in range(i+1, len(industry_correlation.columns)):
            corr_value = industry_correlation.iloc[i, j]
            if abs(corr_value) < 0.3:
                low_corr_pairs.append((industry_correlation.columns[i], 
                                      industry_correlation.columns[j], corr_value))
    
    if low_corr_pairs:
        print("   建议配置以下低相关性行业组合以降低整体风险:")
        for pair in low_corr_pairs[:3]:  # 显示前3对
            print(f"   - {pair[0]} & {pair[1]}: 相关性 {pair[2]:.2f}")
    
    # 3. 风险控制建议
    print("\n3. 风险控制建议:")
    
    # 分析最大回撤
    max_drawdown_analysis = []
    for industry in industry_performance.index:
        max_dd = industry_performance.loc[industry, ('最大回撤(%)', 'mean')]
        max_drawdown_analysis.append((industry, max_dd))
    
    max_drawdown_analysis.sort(key=lambda x: x[1])
    
    print("   基于最大回撤的风险等级:")
    for i, (industry, max_dd) in enumerate(max_drawdown_analysis):
        risk_level = "低风险" if max_dd > -20 else ("中风险" if max_dd > -40 else "高风险")
        print(f"   - {industry}: 平均最大回撤 {max_dd:.1f}% ({risk_level})")
    
    # 4. 未来展望
    print("\n4. 未来展望:")
    
    # 分析趋势
    latest_year = yearly_df['年份'].max()
    prev_year = latest_year - 1
    
    latest_data = yearly_df[yearly_df['年份'] == latest_year]
    prev_data = yearly_df[yearly_df['年份'] == prev_year]
    
    if len(latest_data) > 0 and len(prev_data) > 0:
        latest_avg_vol = latest_data['年化波动率(%)'].mean()
        prev_avg_vol = prev_data['年化波动率(%)'].mean()
        
        vol_trend = "上升" if latest_avg_vol > prev_avg_vol else "下降"
        print(f"   市场波动率趋势: {prev_year}年 {prev_avg_vol:.1f}% → {latest_year}年 {latest_avg_vol:.1f}% ({vol_trend}趋势)")
        
        latest_avg_return = latest_data['年度收益率(%)'].mean()
        prev_avg_return = prev_data['年度收益率(%)'].mean()
        
        return_trend = "改善" if latest_avg_return > prev_avg_return else "恶化"
        print(f"   市场收益率趋势: {prev_year}年 {prev_avg_return:.1f}% → {latest_year}年 {latest_avg_return:.1f}% ({return_trend}趋势)")
    
    # 5. 具体投资策略建议
    print("\n5. 具体投资策略建议:")
    print("   a) 保守型投资者:")
    print("      - 重点配置: 消费龙头、家电龙头等低波动行业")
    print("      - 建议仓位: 70%稳健资产 + 30%现金/债券")
    print("      - 风险控制: 设置-15%止损线")
    
    print("\n   b) 平衡型投资者:")
    print("      - 重点配置: 互联网平台、科技龙头等中等波动行业")
    print("      - 建议仓位: 50%稳健资产 + 40%成长资产 + 10%现金")
    print("      - 风险控制: 设置-25%止损线，定期再平衡")
    
    print("\n   c) 进取型投资者:")
    print("      - 重点配置: 新能源汽车、新能源龙头等高增长行业")
    print("      - 建议仓位: 30%稳健资产 + 60%成长资产 + 10%现金")
    print("      - 风险控制: 设置-35%止损线，采用分批建仓策略")
    
    return recommendations

# ==========================================
# 7. 主函数
# ==========================================
def main():
    """主函数"""
    print("=" * 80)
    print("中概股波动成因深度分析系统 (2023-2026)")
    print("=" * 80)
    
    try:
        # 1. 加载数据
        print("\n1. 数据加载...")
        all_stocks_data, stock_info = load_all_stock_data()
        macro_data = load_macro_data()
        
        if not all_stocks_data:
            print("错误: 没有找到股票数据文件!")
            return
        
        # 2. 缺失值分析
        print("\n2. 数据质量检查...")
        missing_df = analyze_missing_values(all_stocks_data)
        
        # 3. 年度波动分析
        print("\n3. 多维度波动分析...")
        yearly_df = analyze_volatility_by_year(all_stocks_data, stock_info)
        
        # 4. 波动成因分析
        analyze_volatility_causes(yearly_df, macro_data)
        
        # 5. 行业差异分析
        industry_performance, industry_correlation = analyze_industry_differences(yearly_df)
        
        # 6. 可视化分析
        create_visualizations(yearly_df, industry_performance)
        
        # 7. 生成展望和建议
        recommendations = generate_recommendations(yearly_df, industry_performance, industry_correlation)
        
        # 8. 生成最终报告
        generate_final_report(yearly_df, missing_df, industry_performance, industry_correlation)
        
        print("\n" + "=" * 80)
        print("分析完成! 所有结果已保存到文件。")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n程序执行出错: {e}")
        import traceback
        traceback.print_exc()

def generate_final_report(yearly_df, missing_df, industry_performance, industry_correlation):
    """生成最终分析报告"""
    print("\n" + "=" * 60)
    print("生成最终分析报告")
    print("=" * 60)
    
    report_content = []
    
    # 报告头部
    report_content.append("# 中概股波动成因深度分析报告 (2023-2026)")
    report_content.append("")
    report_content.append("## 1. 数据概况")
    report_content.append(f"- 分析股票数量: {len(yearly_df['股票代码'].unique())}")
    report_content.append(f"- 分析时间范围: 2023-2026年")
    report_content.append(f"- 总数据记录: {len(yearly_df)} 条年度数据")
    report_content.append("")
    
    # 数据质量
    report_content.append("## 2. 数据质量分析")
    report_content.append("### 缺失值统计")
    report_content.append(missing_df.to_markdown(index=False))
    report_content.append("")
    
    # 年度表现
    report_content.append("## 3. 年度表现分析")
    yearly_summary = yearly_df.groupby('年份').agg({
        '年度收益率(%)': ['mean', 'std', 'min', 'max'],
        '年化波动率(%)': 'mean',
        '最大回撤(%)': 'mean'
    }).round(2)
    report_content.append(yearly_summary.to_markdown())
    report_content.append("")
    
    # 行业表现
    report_content.append("## 4. 行业差异分析")
    report_content.append("### 各行业综合表现")
    report_content.append(industry_performance.to_markdown())
    report_content.append("")
    
    # 相关性分析
    report_content.append("### 行业收益率相关性")
    report_content.append(industry_correlation.round(2).to_markdown())
    report_content.append("")
    
    # 关键发现
    report_content.append("## 5. 关键发现")
    
    # 找出最佳和最差表现行业
    best_industry = industry_performance[('年度收益率(%)', 'mean')].idxmax()
    worst_industry = industry_performance[('年度收益率(%)', 'mean')].idxmin()
    best_return = industry_performance.loc[best_industry, ('年度收益率(%)', 'mean')]
    worst_return = industry_performance.loc[worst_industry, ('年度收益率(%)', 'mean')]
    
    report_content.append(f"1. **表现最佳行业**: {best_industry} (平均收益率: {best_return:.1f}%)")
    report_content.append(f"2. **表现最差行业**: {worst_industry} (平均收益率: {worst_return:.1f}%)")
    
    # 波动性分析
    highest_vol_industry = industry_performance[('年化波动率(%)', 'mean')].idxmax()
    lowest_vol_industry = industry_performance[('年化波动率(%)', 'mean')].idxmin()
    highest_vol = industry_performance.loc[highest_vol_industry, ('年化波动率(%)', 'mean')]
    lowest_vol = industry_performance.loc[lowest_vol_industry, ('年化波动率(%)', 'mean')]
    
    report_content.append(f"3. **最高波动行业**: {highest_vol_industry} (平均波动率: {highest_vol:.1f}%)")
    report_content.append(f"4. **最低波动行业**: {lowest_vol_industry} (平均波动率: {lowest_vol:.1f}%)")
    report_content.append("")
    
    # 投资建议
    report_content.append("## 6. 投资建议")
    report_content.append("### 6.1 保守型策略")
    report_content.append("- **重点配置**: 消费龙头、家电龙头")
    report_content.append("- **建议仓位**: 70%稳健资产 + 30%现金/债券")
    report_content.append("- **风险控制**: 设置-15%止损线")
    report_content.append("")
    
    report_content.append("### 6.2 平衡型策略")
    report_content.append("- **重点配置**: 互联网平台、科技龙头")
    report_content.append("- **建议仓位**: 50%稳健资产 + 40%成长资产 + 10%现金")
    report_content.append("- **风险控制**: 设置-25%止损线，每季度再平衡")
    report_content.append("")
    
    report_content.append("### 6.3 进取型策略")
    report_content.append("- **重点配置**: 新能源汽车、新能源龙头")
    report_content.append("- **建议仓位**: 30%稳健资产 + 60%成长资产 + 10%现金")
    report_content.append("- **风险控制**: 设置-35%止损线，采用金字塔建仓法")
    report_content.append("")
    
    # 未来展望
    report_content.append("## 7. 未来展望")
    report_content.append("1. **市场趋势**: 基于2023-2026年数据分析，市场整体呈现结构性分化特征")
    report_content.append("2. **行业轮动**: 建议关注互联网平台和新能源汽车的估值修复机会")
    report_content.append("3. **风险提示**: 需警惕新能源行业的高波动性和最大回撤风险")
    report_content.append("4. **配置建议**: 采用行业分散和动态再平衡策略应对市场不确定性")
    report_content.append("")
    
    report_content.append("---")
    report_content.append("**报告生成时间**: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    report_content.append("**数据来源**: AKshare金融数据接口")
    report_content.append("**分析工具**: Python + Pandas + Matplotlib")
    
    # 保存报告
    report_text = "\n".join(report_content)
    with open('china_concept_stocks_analysis_report.md', 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print("✓ 生成最终分析报告: china_concept_stocks_analysis_report.md")

if __name__ == "__main__":
    main()
    
