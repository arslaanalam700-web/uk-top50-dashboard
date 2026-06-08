"""
UK Top 50 Spotify Playlist — Atlantic Recording Corporation
Live Analytics Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="UK Top 50 | Atlantic Recording Corp",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #F7F9FC; }
    .block-container { padding-top: 1.5rem; }
    .stMetric { background: white; border-radius: 10px; padding: 1rem; border: 1px solid #E2E8F0; }
    .stMetric label { font-size: 0.78rem !important; color: #718096 !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.05em; }
    .stMetric [data-testid="metric-container"] { background: white; border-radius: 10px; padding: 1rem; border: 1px solid #E2E8F0; }
    h1 { color: #1F3F7A !important; }
    h2 { color: #1F3F7A !important; }
    h3 { color: #2E75B6 !important; }
    .sidebar .sidebar-content { background: #1F3F7A; }
    div[data-testid="metric-container"] { background-color: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px 16px; }
</style>
""", unsafe_allow_html=True)

# ── DATA LOADING ─────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("Atlantic_United_Kingdom - Atlantic_United_Kingdom.csv")
    df['date'] = pd.to_datetime(df['date'], dayfirst=True)
    df['duration_min'] = df['duration_ms'] / 60000
    df['is_collab'] = df['artist'].str.contains(r'&|feat\.|ft\.', case=False, regex=True)
    df['rank_group'] = pd.cut(df['position'], bins=[0,10,20,30,40,50],
                              labels=['Top 10','11-20','21-30','31-40','41-50'])
    df['month'] = df['date'].dt.to_period('M').astype(str)
    df['year_month'] = df['date'].dt.strftime('%b %Y')
    df['dur_bucket'] = pd.cut(df['duration_min'],
                               bins=[0,2,3,4,5,20],
                               labels=['<2 min','2-3 min','3-4 min','4-5 min','>5 min'])
    df['track_size'] = pd.cut(df['total_tracks'],
                               bins=[0,1,5,15,30,120],
                               labels=['Single (1)','EP (2-5)','Small Album (6-15)','Large Album (16-30)','Mega Album (30+)'])
    return df

df = load_data()

# ── SIDEBAR FILTERS ───────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Atlantic_Records_logo.svg/320px-Atlantic_Records_logo.svg.png", width=180)
    st.markdown("---")
    st.markdown("### Filters")

    date_min = df['date'].min().date()
    date_max = df['date'].max().date()
    date_range = st.date_input("Date range", value=(date_min, date_max),
                               min_value=date_min, max_value=date_max)

    album_filter = st.multiselect("Release format", options=['album','single','compilation'],
                                  default=['album','single','compilation'])

    content_filter = st.radio("Content type", ["All", "Explicit only", "Clean only"])

    collab_filter = st.radio("Collaboration", ["All", "Solo only", "Collaboration only"])

    top_n = st.slider("Top N artists to display", min_value=5, max_value=20, value=15, step=1)

    st.markdown("---")
    st.markdown("**Dataset**")
    st.caption(f"📅 {df['date'].min().strftime('%d %b %Y')} → {df['date'].max().strftime('%d %b %Y')}")
    st.caption(f"📊 {len(df):,} total entries")
    st.caption(f"🎵 {df['artist'].nunique()} unique artists")

# ── APPLY FILTERS ─────────────────────────────────────────────────────────────
fdf = df.copy()
if len(date_range) == 2:
    fdf = fdf[(fdf['date'].dt.date >= date_range[0]) & (fdf['date'].dt.date <= date_range[1])]
if album_filter:
    fdf = fdf[fdf['album_type'].isin(album_filter)]
if content_filter == "Explicit only":
    fdf = fdf[fdf['is_explicit'] == True]
elif content_filter == "Clean only":
    fdf = fdf[fdf['is_explicit'] == False]
if collab_filter == "Solo only":
    fdf = fdf[fdf['is_collab'] == False]
elif collab_filter == "Collaboration only":
    fdf = fdf[fdf['is_collab'] == True]

# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("# 🇬🇧 UK Top 50 — Market Intelligence Dashboard")
st.markdown("**Atlantic Recording Corporation** | UK Market Structure, Artist Diversity & Content Analysis")
st.markdown("---")

# ── KPI METRICS ───────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5, k6 = st.columns(6)

total = len(fdf)
unique_art = fdf['artist'].nunique()
top5_share = fdf['artist'].value_counts().head(5).sum() / total * 100
collab_rate = fdf['is_collab'].mean() * 100
explicit_rate = fdf['is_explicit'].mean() * 100
avg_dur = fdf['duration_min'].mean()
diversity = fdf.groupby('date')['artist'].nunique().mean() / 50 * 100

k1.metric("Total Entries", f"{total:,}")
k2.metric("Unique Artists", f"{unique_art}")
k3.metric("Market Concentration", f"{top5_share:.1f}%", help="Top 5 artists' share of all entries")
k4.metric("Collaboration Rate", f"{collab_rate:.1f}%")
k5.metric("Explicit Share", f"{explicit_rate:.1f}%")
k6.metric("Diversity Score", f"{diversity:.1f}%", help="Avg unique artists per day / 50")

st.markdown("---")

# ── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 Artist Dominance", "🤝 Collaboration Network",
    "🔞 Explicit Content", "💿 Release Format", "⏱️ Track Duration"
])

# ══ TAB 1: ARTIST DOMINANCE ══════════════════════════════════════════════════
with tab1:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Artist Appearance Leaderboard")
        top_artists = fdf['artist'].value_counts().head(top_n).reset_index()
        top_artists.columns = ['Artist', 'Appearances']
        top_artists['% of entries'] = (top_artists['Appearances'] / total * 100).round(2)

        fig = px.bar(top_artists, x='Appearances', y='Artist', orientation='h',
                     color='Appearances', color_continuous_scale='Blues',
                     text='Appearances', hover_data=['% of entries'])
        fig.update_traces(textposition='outside', textfont_size=11)
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=500,
                          showlegend=False, coloraxis_showscale=False,
                          plot_bgcolor='white', paper_bgcolor='white',
                          margin=dict(l=0, r=20, t=20, b=20))
        fig.update_xaxes(showgrid=True, gridcolor='#F0F0F0')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Top 10 Songs")
        top_songs = (fdf.groupby(['song','artist'])
                     .agg(days=('song','count'), avg_rank=('position','mean'))
                     .sort_values('days', ascending=False)
                     .head(10)
                     .reset_index())
        top_songs['avg_rank'] = top_songs['avg_rank'].round(1)
        for _, row in top_songs.iterrows():
            with st.container():
                st.markdown(f"**{row['song']}**")
                st.caption(f"{row['artist'][:35]}{'...' if len(row['artist'])>35 else ''} · {row['days']} days · avg #{row['avg_rank']:.0f}")

    st.markdown("---")
    st.subheader("Monthly Unique Artist Diversity")
    monthly_diversity = fdf.groupby('month')['artist'].nunique().reset_index()
    monthly_diversity.columns = ['Month', 'Unique Artists']
    fig2 = px.area(monthly_diversity, x='Month', y='Unique Artists',
                   color_discrete_sequence=['#2E75B6'], markers=True)
    fig2.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                       height=280, margin=dict(l=0, r=0, t=10, b=40))
    fig2.update_xaxes(tickangle=45, showgrid=False)
    fig2.update_yaxes(showgrid=True, gridcolor='#F0F0F0')
    st.plotly_chart(fig2, use_container_width=True)

# ══ TAB 2: COLLABORATION ══════════════════════════════════════════════════════
with tab2:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Collaboration Rate by Rank Band")
        collab_rank = fdf.groupby('rank_group')['is_collab'].mean().reset_index()
        collab_rank.columns = ['Rank Band', 'Collab Rate']
        collab_rank['Collab Rate %'] = (collab_rank['Collab Rate'] * 100).round(1)

        fig = px.bar(collab_rank, x='Rank Band', y='Collab Rate %',
                     color='Collab Rate %', color_continuous_scale='Oranges',
                     text='Collab Rate %')
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', height=380,
                          showlegend=False, coloraxis_showscale=False,
                          margin=dict(l=0, r=0, t=20, b=20))
        fig.update_yaxes(range=[0, 30], showgrid=True, gridcolor='#F0F0F0')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Solo vs Collaboration: Avg Chart Position")
        solo_avg = fdf[~fdf['is_collab']]['position'].mean()
        collab_avg = fdf[fdf['is_collab']]['position'].mean()

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=['Solo', 'Collaboration'],
                              y=[solo_avg, collab_avg],
                              marker_color=['#2E75B6','#EF9F27'],
                              text=[f"{solo_avg:.2f}", f"{collab_avg:.2f}"],
                              textposition='outside'))
        fig2.update_layout(plot_bgcolor='white', paper_bgcolor='white', height=380,
                           yaxis_title="Avg Chart Position (lower = better)",
                           yaxis=dict(range=[0, 35], showgrid=True, gridcolor='#F0F0F0'),
                           margin=dict(l=0, r=0, t=20, b=20))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.subheader("Top Collaborative Tracks")
    collabs = fdf[fdf['is_collab']].groupby(['song','artist']).agg(
        appearances=('song','count'), avg_rank=('position','mean')
    ).sort_values('appearances', ascending=False).head(10).reset_index()
    collabs['avg_rank'] = collabs['avg_rank'].round(1)
    collabs.columns = ['Song', 'Artists', 'Appearances', 'Avg Rank']
    st.dataframe(collabs, use_container_width=True, hide_index=True)

# ══ TAB 3: EXPLICIT CONTENT ═══════════════════════════════════════════════════
with tab3:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Explicit vs Clean by Rank Band")
        exp_rank = fdf.groupby('rank_group')['is_explicit'].agg(['mean','count']).reset_index()
        exp_rank['Explicit %'] = (exp_rank['mean'] * 100).round(1)
        exp_rank['Clean %'] = (100 - exp_rank['Explicit %']).round(1)

        fig = go.Figure()
        fig.add_trace(go.Bar(name='Explicit', x=exp_rank['rank_group'].astype(str),
                             y=exp_rank['Explicit %'], marker_color='#D85A30',
                             text=exp_rank['Explicit %'], texttemplate='%{text:.1f}%'))
        fig.add_trace(go.Bar(name='Clean', x=exp_rank['rank_group'].astype(str),
                             y=exp_rank['Clean %'], marker_color='#639922',
                             text=exp_rank['Clean %'], texttemplate='%{text:.1f}%'))
        fig.update_layout(barmode='stack', plot_bgcolor='white', paper_bgcolor='white',
                          height=380, margin=dict(l=0, r=0, t=20, b=20),
                          legend=dict(orientation='h', yanchor='bottom', y=1.02))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Monthly Explicit Content Trend")
        monthly_exp = fdf.groupby('month')['is_explicit'].mean().reset_index()
        monthly_exp.columns = ['Month', 'Explicit Rate']
        monthly_exp['Explicit %'] = (monthly_exp['Explicit Rate'] * 100).round(1)

        fig2 = px.line(monthly_exp, x='Month', y='Explicit %',
                       color_discrete_sequence=['#D85A30'], markers=True)
        fig2.add_hline(y=monthly_exp['Explicit %'].mean(), line_dash='dash',
                       line_color='#888888', annotation_text=f"Avg {monthly_exp['Explicit %'].mean():.1f}%")
        fig2.update_layout(plot_bgcolor='white', paper_bgcolor='white', height=380,
                           margin=dict(l=0, r=0, t=20, b=40))
        fig2.update_xaxes(tickangle=45, showgrid=False)
        fig2.update_yaxes(showgrid=True, gridcolor='#F0F0F0')
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Explicit Rate by Release Format")
        exp_format = fdf.groupby('album_type')['is_explicit'].mean().reset_index()
        exp_format.columns = ['Format', 'Rate']
        exp_format['Explicit %'] = (exp_format['Rate'] * 100).round(1)
        fig3 = px.bar(exp_format, x='Format', y='Explicit %',
                      color='Format', color_discrete_map={'album':'#378ADD','single':'#534AB7','compilation':'#888780'},
                      text='Explicit %')
        fig3.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig3.update_layout(plot_bgcolor='white', paper_bgcolor='white', height=320,
                           showlegend=False, margin=dict(l=0, r=0, t=20, b=20))
        fig3.update_yaxes(range=[0, 50], showgrid=True, gridcolor='#F0F0F0')
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.subheader("Key Explicit Insight")
        st.info("🔞 **Top 10 has the highest explicit rate (40.4%)** — explicit content does not penalise premium chart positions in the UK.")
        st.warning("📅 **December exception**: Explicit share falls to **15.0%** in December — festive programming suppresses explicit content.")
        st.success("📈 **Best explicit launch window**: February–March (43.6% / 41.8%) for maximum editorial receptivity.")

# ══ TAB 4: RELEASE FORMAT ═════════════════════════════════════════════════════
with tab4:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Format Distribution (Volume)")
        format_dist = fdf['album_type'].value_counts().reset_index()
        format_dist.columns = ['Format', 'Count']
        fig = px.pie(format_dist, names='Format', values='Count',
                     color='Format', color_discrete_map={'album':'#378ADD','single':'#534AB7','compilation':'#888780'},
                     hole=0.5)
        fig.update_traces(textposition='outside', textinfo='percent+label')
        fig.update_layout(height=380, margin=dict(l=20, r=20, t=20, b=20),
                          showlegend=False, paper_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Avg Chart Position by Format")
        rank_format = fdf.groupby('album_type')['position'].mean().reset_index()
        rank_format.columns = ['Format', 'Avg Position']
        rank_format['Avg Position'] = rank_format['Avg Position'].round(2)
        rank_format['Performance'] = rank_format['Avg Position'].apply(
            lambda x: f"#{x:.1f} avg" )

        fig2 = px.bar(rank_format, x='Format', y='Avg Position',
                      color='Format',
                      color_discrete_map={'album':'#378ADD','single':'#534AB7','compilation':'#888780'},
                      text='Avg Position')
        fig2.update_traces(texttemplate='#%{text:.1f}', textposition='outside')
        fig2.update_layout(plot_bgcolor='white', paper_bgcolor='white', height=380,
                           yaxis_title="Avg Position (lower = better)",
                           yaxis=dict(autorange='reversed', range=[35, 18],
                                      showgrid=True, gridcolor='#F0F0F0'),
                           showlegend=False, margin=dict(l=0, r=0, t=20, b=20))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.subheader("Album Size vs Chart Presence")
    size_dist = fdf['track_size'].value_counts().sort_index().reset_index()
    size_dist.columns = ['Album Size', 'Chart Entries']
    fig3 = px.bar(size_dist, x='Album Size', y='Chart Entries',
                  color='Chart Entries', color_continuous_scale='Blues',
                  text='Chart Entries')
    fig3.update_traces(textposition='outside')
    fig3.update_layout(plot_bgcolor='white', paper_bgcolor='white', height=320,
                       coloraxis_showscale=False, margin=dict(l=0, r=0, t=20, b=20))
    fig3.update_yaxes(showgrid=True, gridcolor='#F0F0F0')
    st.plotly_chart(fig3, use_container_width=True)

# ══ TAB 5: TRACK DURATION ═════════════════════════════════════════════════════
with tab5:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Duration Distribution")
        dur_dist = fdf['dur_bucket'].value_counts().sort_index().reset_index()
        dur_dist.columns = ['Duration', 'Count']
        dur_dist['%'] = (dur_dist['Count'] / dur_dist['Count'].sum() * 100).round(1)

        fig = px.bar(dur_dist, x='Duration', y='Count',
                     color='Count', color_continuous_scale='Purples',
                     text='%')
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', height=380,
                          coloraxis_showscale=False, margin=dict(l=0, r=0, t=20, b=20))
        fig.update_yaxes(showgrid=True, gridcolor='#F0F0F0')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Duration vs Avg Popularity")
        dur_pop = fdf.groupby('dur_bucket').agg(
            avg_popularity=('popularity','mean'),
            count=('song','count')
        ).reset_index()
        dur_pop['avg_popularity'] = dur_pop['avg_popularity'].round(2)

        fig2 = px.scatter(dur_pop, x='dur_bucket', y='avg_popularity',
                          size='count', color='avg_popularity',
                          color_continuous_scale='Blues',
                          text='avg_popularity', size_max=60)
        fig2.update_traces(textposition='top center', texttemplate='%{text:.1f}')
        fig2.update_layout(plot_bgcolor='white', paper_bgcolor='white', height=380,
                           xaxis_title="Duration Bucket", yaxis_title="Avg Popularity Score",
                           coloraxis_showscale=False, margin=dict(l=0, r=0, t=20, b=20))
        fig2.update_yaxes(range=[80, 92], showgrid=True, gridcolor='#F0F0F0')
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    col3, col4, col5 = st.columns(3)
    col3.metric("Average Duration", f"{fdf['duration_min'].mean():.2f} min")
    col4.metric("Most Common Bucket", "3-4 minutes", "44% of chart entries")
    col5.metric("Shortest Track", f"{fdf['duration_min'].min():.2f} min")

    st.info("🎵 **UK Production Brief**: Target 2:45–3:30 master length for maximum UK chart and radio compatibility. Tracks under 4 minutes represent 80.8% of all chart entries.")

# ── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#718096; font-size:0.8rem;'>"
    "Atlantic Recording Corporation · UK Market Intelligence Unit · "
    f"Data: 18 May 2024 – 30 Nov 2025 · {len(df):,} entries · 343 unique artists · "
    "Classification: Confidential"
    "</div>",
    unsafe_allow_html=True
)
