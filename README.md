# 🚀 Startup Funding Dashboard

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458?logo=pandas)
![Plotly](https://img.shields.io/badge/Plotly-Interactive%20Charts-3F4F75?logo=plotly)

An interactive **Streamlit Dashboard** for exploring the **Indian Startup Funding** dataset. The application provides startup-wise, investor-wise, and overall funding analysis through interactive visualizations and business insights.

---

## 📌 Features

### 📊 Overall Analysis
- 💰 Total Funding Raised
- 🏢 Total Funded Startups
- 📈 Largest Funding Round
- 💵 Average Funding Amount
- 📅 Monthly Funding Trends
- 🏆 Top 10 Funded Startups
- 🏭 Top Sectors by Funding
- 🤝 Top Investors by Deal Count

### 🚀 Startup Analysis
- Startup Profile
- Total Capital Raised
- Number of Funding Rounds
- Industry & Sub-Industry
- Headquarters City
- Complete Funding History
- Funding Timeline

### 💼 Investor Analysis
- Recent Investments
- Largest Investments
- Sector-wise Investment Distribution
- Funding Stage Analysis
- City-wise Portfolio
- Year-wise Investment Trend

### 📈 Interactive Visualizations
- Plotly Charts
- Hover Tooltips
- Zoom & Pan Support
- Dynamic Filtering

---

## 🧹 Data Cleaning

The dataset was preprocessed before visualization by:

- Removing unwanted whitespace and encoding issues
- Standardizing investor names using fuzzy matching
- Handling missing values
- Cleaning categorical data
- Optimizing loading performance using `st.cache_data`

---

## 🛠 Tech Stack

- Python
- Streamlit
- Pandas
- Plotly

---

## 📂 Dataset

The project uses the **Indian Startup Funding Dataset** containing information such as:

- Startup Name
- Industry
- City
- Investors
- Funding Round
- Funding Amount
- Funding Date

---

## 🚀 Run Locally

Clone the repository

```bash
git clone https://github.com/Sawi2005/Startup_Funding.git
```

Go to the project directory

```bash
cd startup_dasboard
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the application

```bash
streamlit run app.py
```

---

## 📁 Project Structure

```
startup_dasboard/
│
├── app.py
├── startup_clear.csv
├── requirements.txt
└── README.md
```

---

## ⭐ Highlights

- Interactive startup funding analysis
- Investor portfolio insights
- Startup funding history
- Dynamic Plotly visualizations
- Fast and responsive Streamlit application
- Clean and intuitive user interface

---

## 🔮 Future Improvements

- Startup funding prediction using Machine Learning
- Live data integration
- Advanced search and filtering
- Cloud deployment

---

## 👨‍💻 Author

**Sawi Trehan**

If you found this project useful, don't forget to ⭐ the repository!
