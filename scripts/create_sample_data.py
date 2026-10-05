import os
import pandas as pd

os.makedirs("data", exist_ok=True)
os.makedirs("output", exist_ok=True)

# 1. Sales KPI Dataset
sales_data = [
    {"Period": "2024-01", "Region": "North America", "Product_Line": "Enterprise SaaS", "Revenue": 1250000, "Target_Revenue": 1200000, "Gross_Margin_Pct": 78.5, "New_Customers": 45, "CAC": 4200, "Conversion_Rate_Pct": 3.8, "Churn_Rate_Pct": 1.2},
    {"Period": "2024-02", "Region": "North America", "Product_Line": "Enterprise SaaS", "Revenue": 1310000, "Target_Revenue": 1250000, "Gross_Margin_Pct": 79.1, "New_Customers": 49, "CAC": 4100, "Conversion_Rate_Pct": 4.1, "Churn_Rate_Pct": 1.1},
    {"Period": "2024-03", "Region": "North America", "Product_Line": "Enterprise SaaS", "Revenue": 1420000, "Target_Revenue": 1300000, "Gross_Margin_Pct": 80.2, "New_Customers": 58, "CAC": 3950, "Conversion_Rate_Pct": 4.5, "Churn_Rate_Pct": 0.9},
    {"Period": "2024-04", "Region": "North America", "Product_Line": "Enterprise SaaS", "Revenue": 1380000, "Target_Revenue": 1350000, "Gross_Margin_Pct": 78.8, "New_Customers": 52, "CAC": 4300, "Conversion_Rate_Pct": 4.0, "Churn_Rate_Pct": 1.4},
    {"Period": "2024-05", "Region": "North America", "Product_Line": "Enterprise SaaS", "Revenue": 1510000, "Target_Revenue": 1400000, "Gross_Margin_Pct": 81.0, "New_Customers": 64, "CAC": 3800, "Conversion_Rate_Pct": 4.7, "Churn_Rate_Pct": 0.8},
    {"Period": "2024-06", "Region": "North America", "Product_Line": "Enterprise SaaS", "Revenue": 1680000, "Target_Revenue": 1450000, "Gross_Margin_Pct": 82.4, "New_Customers": 72, "CAC": 3650, "Conversion_Rate_Pct": 5.2, "Churn_Rate_Pct": 0.7},

    {"Period": "2024-01", "Region": "EMEA", "Product_Line": "Enterprise SaaS", "Revenue": 820000, "Target_Revenue": 850000, "Gross_Margin_Pct": 72.0, "New_Customers": 28, "CAC": 5100, "Conversion_Rate_Pct": 2.9, "Churn_Rate_Pct": 1.8},
    {"Period": "2024-02", "Region": "EMEA", "Product_Line": "Enterprise SaaS", "Revenue": 840000, "Target_Revenue": 860000, "Gross_Margin_Pct": 72.5, "New_Customers": 30, "CAC": 5000, "Conversion_Rate_Pct": 3.0, "Churn_Rate_Pct": 1.7},
    {"Period": "2024-03", "Region": "EMEA", "Product_Line": "Enterprise SaaS", "Revenue": 890000, "Target_Revenue": 880000, "Gross_Margin_Pct": 73.1, "New_Customers": 34, "CAC": 4850, "Conversion_Rate_Pct": 3.2, "Churn_Rate_Pct": 1.5},
    {"Period": "2024-04", "Region": "EMEA", "Product_Line": "Enterprise SaaS", "Revenue": 810000, "Target_Revenue": 900000, "Gross_Margin_Pct": 70.8, "New_Customers": 26, "CAC": 5400, "Conversion_Rate_Pct": 2.7, "Churn_Rate_Pct": 2.1},
    {"Period": "2024-05", "Region": "EMEA", "Product_Line": "Enterprise SaaS", "Revenue": 860000, "Target_Revenue": 920000, "Gross_Margin_Pct": 71.9, "New_Customers": 31, "CAC": 5200, "Conversion_Rate_Pct": 2.9, "Churn_Rate_Pct": 1.9},
    {"Period": "2024-06", "Region": "EMEA", "Product_Line": "Enterprise SaaS", "Revenue": 920000, "Target_Revenue": 950000, "Gross_Margin_Pct": 73.5, "New_Customers": 35, "CAC": 4900, "Conversion_Rate_Pct": 3.3, "Churn_Rate_Pct": 1.6},

    {"Period": "2024-01", "Region": "APAC", "Product_Line": "Enterprise SaaS", "Revenue": 510000, "Target_Revenue": 500000, "Gross_Margin_Pct": 68.0, "New_Customers": 22, "CAC": 3900, "Conversion_Rate_Pct": 3.1, "Churn_Rate_Pct": 1.5},
    {"Period": "2024-02", "Region": "APAC", "Product_Line": "Enterprise SaaS", "Revenue": 540000, "Target_Revenue": 520000, "Gross_Margin_Pct": 69.2, "New_Customers": 25, "CAC": 3800, "Conversion_Rate_Pct": 3.4, "Churn_Rate_Pct": 1.4},
    {"Period": "2024-03", "Region": "APAC", "Product_Line": "Enterprise SaaS", "Revenue": 610000, "Target_Revenue": 550000, "Gross_Margin_Pct": 70.5, "New_Customers": 31, "CAC": 3600, "Conversion_Rate_Pct": 3.9, "Churn_Rate_Pct": 1.2},
    {"Period": "2024-04", "Region": "APAC", "Product_Line": "Enterprise SaaS", "Revenue": 640000, "Target_Revenue": 580000, "Gross_Margin_Pct": 71.0, "New_Customers": 33, "CAC": 3550, "Conversion_Rate_Pct": 4.0, "Churn_Rate_Pct": 1.1},
    {"Period": "2024-05", "Region": "APAC", "Product_Line": "Enterprise SaaS", "Revenue": 690000, "Target_Revenue": 600000, "Gross_Margin_Pct": 72.4, "New_Customers": 38, "CAC": 3400, "Conversion_Rate_Pct": 4.3, "Churn_Rate_Pct": 1.0},
    {"Period": "2024-06", "Region": "APAC", "Product_Line": "Enterprise SaaS", "Revenue": 760000, "Target_Revenue": 630000, "Gross_Margin_Pct": 73.8, "New_Customers": 44, "CAC": 3250, "Conversion_Rate_Pct": 4.8, "Churn_Rate_Pct": 0.8},
]

df_sales = pd.DataFrame(sales_data)
df_sales.to_csv("data/sample_kpi_sales.csv", index=False)
print("Saved data/sample_kpi_sales.csv")

# 2. Marketing KPI Dataset
marketing_data = [
    {"Period": "2024-05", "Channel": "Google Search Ads", "Ad_Spend": 45000, "Impressions": 920000, "Clicks": 41400, "Leads": 1860, "CAC": 142.5, "ROAS": 3.8, "Conversion_Rate_Pct": 4.5},
    {"Period": "2024-06", "Channel": "Google Search Ads", "Ad_Spend": 52000, "Impressions": 1150000, "Clicks": 54050, "Leads": 2540, "CAC": 128.2, "ROAS": 4.4, "Conversion_Rate_Pct": 4.7},
    {"Period": "2024-05", "Channel": "Paid Social (Meta)", "Ad_Spend": 38000, "Impressions": 1450000, "Clicks": 36250, "Leads": 1120, "CAC": 182.0, "ROAS": 2.4, "Conversion_Rate_Pct": 3.1},
    {"Period": "2024-06", "Channel": "Paid Social (Meta)", "Ad_Spend": 35000, "Impressions": 1280000, "Clicks": 30720, "Leads": 890, "CAC": 210.5, "ROAS": 1.9, "Conversion_Rate_Pct": 2.9},
    {"Period": "2024-05", "Channel": "LinkedIn B2B", "Ad_Spend": 28000, "Impressions": 320000, "Clicks": 9600, "Leads": 740, "CAC": 265.0, "ROAS": 3.2, "Conversion_Rate_Pct": 7.7},
    {"Period": "2024-06", "Channel": "LinkedIn B2B", "Ad_Spend": 32000, "Impressions": 380000, "Clicks": 12160, "Leads": 980, "CAC": 241.0, "ROAS": 3.7, "Conversion_Rate_Pct": 8.1},
    {"Period": "2024-05", "Channel": "Email & Retention", "Ad_Spend": 6500, "Impressions": 280000, "Clicks": 33600, "Leads": 1640, "CAC": 24.5, "ROAS": 8.6, "Conversion_Rate_Pct": 4.9},
    {"Period": "2024-06", "Channel": "Email & Retention", "Ad_Spend": 7200, "Impressions": 310000, "Clicks": 40300, "Leads": 2080, "CAC": 21.0, "ROAS": 9.4, "Conversion_Rate_Pct": 5.2},
]
df_mkt = pd.DataFrame(marketing_data)
df_mkt.to_csv("data/sample_kpi_marketing.csv", index=False)
print("Saved data/sample_kpi_marketing.csv")

# 3. Operations KPI Dataset (Excel)
ops_data = [
    {"Month": "2024-04", "Warehouse": "US-East (NJ)", "Order_Volume": 84500, "Avg_Fulfillment_Hours": 14.2, "SLA_Breach_Pct": 1.8, "Cost_Per_Unit": 4.85, "Return_Rate_Pct": 3.2},
    {"Month": "2024-05", "Warehouse": "US-East (NJ)", "Order_Volume": 91200, "Avg_Fulfillment_Hours": 13.8, "SLA_Breach_Pct": 1.4, "Cost_Per_Unit": 4.70, "Return_Rate_Pct": 3.0},
    {"Month": "2024-06", "Warehouse": "US-East (NJ)", "Order_Volume": 99400, "Avg_Fulfillment_Hours": 12.5, "SLA_Breach_Pct": 0.9, "Cost_Per_Unit": 4.45, "Return_Rate_Pct": 2.7},
    {"Month": "2024-04", "Warehouse": "US-West (CA)", "Order_Volume": 62000, "Avg_Fulfillment_Hours": 18.5, "SLA_Breach_Pct": 4.2, "Cost_Per_Unit": 5.60, "Return_Rate_Pct": 4.1},
    {"Month": "2024-05", "Warehouse": "US-West (CA)", "Order_Volume": 64800, "Avg_Fulfillment_Hours": 19.8, "SLA_Breach_Pct": 5.1, "Cost_Per_Unit": 5.85, "Return_Rate_Pct": 4.5},
    {"Month": "2024-06", "Warehouse": "US-West (CA)", "Order_Volume": 68200, "Avg_Fulfillment_Hours": 21.2, "SLA_Breach_Pct": 6.8, "Cost_Per_Unit": 6.15, "Return_Rate_Pct": 4.9},
    {"Month": "2024-04", "Warehouse": "EU-Central (DE)", "Order_Volume": 45000, "Avg_Fulfillment_Hours": 15.1, "SLA_Breach_Pct": 2.2, "Cost_Per_Unit": 5.10, "Return_Rate_Pct": 3.4},
    {"Month": "2024-05", "Warehouse": "EU-Central (DE)", "Order_Volume": 47200, "Avg_Fulfillment_Hours": 14.6, "SLA_Breach_Pct": 2.0, "Cost_Per_Unit": 4.95, "Return_Rate_Pct": 3.3},
    {"Month": "2024-06", "Warehouse": "EU-Central (DE)", "Order_Volume": 51000, "Avg_Fulfillment_Hours": 14.0, "SLA_Breach_Pct": 1.7, "Cost_Per_Unit": 4.80, "Return_Rate_Pct": 3.1},
]
df_ops = pd.DataFrame(ops_data)
df_ops.to_excel("data/sample_kpi_operations.xlsx", index=False)
print("Saved data/sample_kpi_operations.xlsx")
