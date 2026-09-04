let balance = Number(localStorage.getItem("rewardrush_balance")) || 0;

const balanceElement = document.getElementById("balance");
const button = document.getElementById("watchAd");
const message = document.getElementById("message");

function updateBalance() {
  balanceElement.textContent = balance;
}

button.addEventListener("click", async () => {
  button.disabled = true;
  message.textContent = "Loading ad...";

  try {
    if (typeof show_11721313 !== "function") {
      throw new Error("Ad SDK is not ready.");
    }

    await show_11721313();

    balance += 1;
    localStorage.setItem("rewardrush_balance", balance);

    updateBalance();
    message.textContent = "✅ Ad completed! You earned 1 RR.";
  } catch (error) {
    message.textContent = "❌ Ad could not be displayed. Please try again.";
  }

  button.disabled = false;
});

updateBalance();
