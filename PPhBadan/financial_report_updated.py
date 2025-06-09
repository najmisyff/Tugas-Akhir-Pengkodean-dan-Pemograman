import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

# Define color scheme
WHITE = '#FFFFFF'
ROSE_GOLD = '#B76E79'
MAROON = '#800000'
GRAY = '#808080'

# Load data from string content (simulating CSV files)
aset_tetap = pd.read_csv(io.StringIO('''aset_id,kategori,nilai_perolehan,umur_ekonomis,metode
A001,Mesin,500000000,10,Garis Lurus
A002,Kendaraan,300000000,5,Garis Lurus
A003,Bangunan,1000000000,20,Saldo Menurun
A004,Peralatan,200000000,8,Garis Lurus
A005,Mesin,750000000,12,Saldo Menurun'''))

kebijakan_fiskal = pd.read_csv(io.StringIO('''tahun,tax_rate,tax_holiday_awal,tax_holiday_akhir
2023,0.22,2023-01-01,2023-12-31
2024,0.22,2024-01-01,2024-12-31
2025,0.20,2025-01-01,2025-12-31
2026,0.20,2026-01-01,2026-12-31
2027,0.20,2027-01-01,2027-12-31'''))

transaksi_keuangan = pd.read_csv(io.StringIO('''tahun,pendapatan,beban_operasional,penyusutan,skenario
2023,1000000000,400000000,50000000,Normal
2024,1100000000,420000000,50000000,Normal
2025,1200000000,440000000,50000000,Normal
2026,1300000000,460000000,50000000,Normal
2027,1400000000,480000000,50000000,Normal
2023,1000000000,400000000,50000000,Tax Holiday
2024,1100000000,420000000,50000000,Tax Holiday
2025,1200000000,440000000,50000000,Tax Holiday
2026,1300000000,460000000,50000000,Tax Holiday
2027,1400000000,480000000,50000000,Tax Holiday
2023,1000000000,400000000,60000000,Perbandingan metode depresiasi
2024,1100000000,420000000,55000000,Perbandingan metode depresiasi
2025,1200000000,440000000,50000000,Perbandingan metode depresiasi
2026,1300000000,460000000,45000000,Perbandingan metode depresiasi
2027,1400000000,480000000,40000000,Perbandingan metode depresiasi'''))

# Calculate depreciation based on method
def calculate_depreciation(row, year):
    nilai = row['nilai_perolehan']
    umur = row['umur_ekonomis']
    metode = row['metode']
    if metode == 'Garis Lurus':
        return nilai / umur
    elif metode == 'Saldo Menurun':
        rate = 2 / umur  # Double declining balance
        book_value = nilai
        for y in range(2023, year + 1):
            book_value -= book_value * rate
        return nilai * rate if book_value > 0 else 0
    return 0

# Calculate total depreciation per year
def get_total_depreciation(year):
    return sum(calculate_depreciation(row, year) for _, row in aset_tetap.iterrows())

# Merge fiscal policy with transactions
transaksi_keuangan = transaksi_keuangan.merge(kebijakan_fiskal[['tahun', 'tax_rate']], on='tahun', how='left')

# Calculate financial metrics (in millions of Rupiah)
transaksi_keuangan['laba_sebelum_pajak'] = (transaksi_keuangan['pendapatan'] - transaksi_keuangan['beban_operasional'] - transaksi_keuangan['penyusutan']) / 1_000_000
transaksi_keuangan['pajak'] = transaksi_keuangan.apply(
    lambda row: 0 if row['skenario'] == 'Tax Holiday' else row['laba_sebelum_pajak'] * row['tax_rate'], axis=1)
transaksi_keuangan['laba_bersih'] = transaksi_keuangan['laba_sebelum_pajak'] - transaksi_keuangan['pajak']
transaksi_keuangan['pendapatan'] = transaksi_keuangan['pendapatan'] / 1_000_000
transaksi_keuangan['beban_operasional'] = transaksi_keuangan['beban_operasional'] / 1_000_000
transaksi_keuangan['penyusutan'] = transaksi_keuangan['penyusutan'] / 1_000_000

# Animated Bar Chart with Dropdown Menu
fig1 = go.Figure()
metrics = ['pendapatan', 'beban_operasional', 'laba_bersih']
for metric in metrics:
    for scenario in transaksi_keuangan['skenario'].unique():
        df = transaksi_keuangan[transaksi_keuangan['skenario'] == scenario]
        fig1.add_trace(
            go.Bar(
                x=df['tahun'],
                y=df[metric],
                name=f'{scenario} - {metric.capitalize()}',
                marker_color=ROSE_GOLD if scenario == 'Tax Holiday' else MAROON if scenario == 'Normal' else GRAY,
                visible=(metric == 'pendapatan')
            )
        )

# Create dropdown menu
buttons = [
    dict(
        label=metric.capitalize(),
        method='update',
        args=[{'visible': [metric == m for m in metrics for _ in transaksi_keuangan['skenario'].unique()]},
              {'title': f'{metric.capitalize()} by Scenario (2023-2027)'}]
    ) for metric in metrics
]

fig1.update_layout(
    updatemenus=[dict(
        buttons=buttons,
        direction='down',
        showactive=True,
        x=0.1,
        xanchor='left',
        y=1.15,
        yanchor='top'
    )],
    title='Revenue by Scenario (2023-2027)',
    xaxis=dict(title='Year', tickmode='linear', tick0=2023, dtick=1),
    yaxis=dict(title='Amount (Million IDR)'),
    barmode='group',
    plot_bgcolor=WHITE,
    paper_bgcolor=WHITE,
    font=dict(color=MAROON)
)

# Pie Chart for Asset Distribution
asset_dist = aset_tetap.groupby('kategori')['nilai_perolehan'].sum().reset_index()
asset_dist['nilai_perolehan'] = asset_dist['nilai_perolehan'] / 1_000_000
fig2 = px.pie(
    asset_dist,
    values='nilai_perolehan',
    names='kategori',
    title='Fixed Asset Distribution (Million IDR)',
    color_discrete_sequence=[ROSE_GOLD, MAROON, GRAY]
)
fig2.update_layout(
    plot_bgcolor=WHITE,
    paper_bgcolor=WHITE,
    font=dict(color=MAROON)
)

# Interesting Fact: Percentage increase in net profit (Normal scenario)
net_profit_2023 = transaksi_keuangan[(transaksi_keuangan['tahun'] == 2023) & (transaksi_keuangan['skenario'] == 'Normal')]['laba_bersih'].iloc[0]
net_profit_2027 = transaksi_keuangan[(transaksi_keuangan['tahun'] == 2027) & (transaksi_keuangan['skenario'] == 'Normal')]['laba_bersih'].iloc[0]
percentage_increase = ((net_profit_2027 - net_profit_2023) / net_profit_2023) * 100
print(f"Interesting Fact: Net profit in the Normal scenario increases by {percentage_increase:.2f}% from 2023 to 2027, showcasing strong financial growth.")

# Summary Table
summary = transaksi_keuangan[['tahun', 'skenario', 'pendapatan', 'beban_operasional', 'penyusutan', 'laba_sebelum_pajak', 'pajak', 'laba_bersih']].copy()
summary = summary.round(2)
print("\nSummary Table (in Million IDR):")
display(summary.style.set_properties(**{'background-color': WHITE, 'color': MAROON, 'border-color': GRAY}))

# Display charts
fig1.show()
fig2.show()