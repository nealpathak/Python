import yfinance as yf
import matplotlib.pyplot as plt

# Get user input for year
year = input("Enter a year (e.g. 2022): ")

# Fetch historical data for the VIX index for the given year
start_date = year + "-01-01"
end_date = year + "-12-31"
data = yf.download("^VIX", start=start_date, end=end_date)

# Plot a line chart of the VIX index
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(data.index, data["Close"], color="blue", linewidth=2)
ax.set_title("VIX Index - " + year, fontsize=18)
ax.set_xlabel("Date", fontsize=14)
ax.set_ylabel("Price (USD)", fontsize=14)
ax.grid(True)
plt.show()