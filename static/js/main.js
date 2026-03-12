const dateInput = document.querySelector("input[name='session_date']");
if (dateInput) {
  const today = new Date().toISOString().split("T")[0];
  dateInput.min = today;
}
