// Tab Navigation Logic
function switchTab(tabName) {
    const panes = document.querySelectorAll('.tab-pane');
    panes.forEach(pane => pane.classList.remove('active'));

    const buttons = document.querySelectorAll('.nav-btn');
    buttons.forEach(btn => btn.classList.remove('active'));

    const activePane = document.getElementById(`tab-${tabName}`);
    if (activePane) {
        activePane.classList.add('active');
    }

    // Update active nav button
    buttons.forEach(btn => {
        if (btn.getAttribute('onclick') && btn.getAttribute('onclick').includes(tabName)) {
            btn.classList.add('active');
        }
    });

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Real-Time Loan Prediction Handler
async function handlePrediction(event) {
    event.preventDefault();

    const form = document.getElementById('loanForm');
    const submitBtn = document.getElementById('submitBtn');
    const placeholder = document.getElementById('resultPlaceholder');
    const content = document.getElementById('resultContent');

    const originalBtnText = submitBtn.innerHTML;
    submitBtn.innerHTML = '⏳ Evaluating Application...';
    submitBtn.disabled = true;

    // Collect Form Values
    const payload = {
        Gender: document.getElementById('Gender').value,
        Married: document.getElementById('Married').value,
        Dependents: document.getElementById('Dependents').value,
        Education: document.getElementById('Education').value,
        Self_Employed: document.getElementById('Self_Employed').value,
        ApplicantIncome: parseFloat(document.getElementById('ApplicantIncome').value) || 0,
        CoapplicantIncome: parseFloat(document.getElementById('CoapplicantIncome').value) || 0,
        LoanAmount: parseFloat(document.getElementById('LoanAmount').value) || 10,
        Loan_Amount_Term: parseFloat(document.getElementById('Loan_Amount_Term').value) || 360,
        Credit_History: parseFloat(document.getElementById('Credit_History').value),
        Property_Area: document.getElementById('Property_Area').value
    };

    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'Prediction failed');
        }

        const data = await response.json();

        // Switch to result display
        placeholder.style.display = 'none';
        content.style.display = 'block';

        const decisionBox = document.getElementById('decisionBanner');
        const decisionTitle = document.getElementById('decisionTitle');
        const decisionSub = document.getElementById('decisionSubtitle');
        const riskBadge = document.getElementById('riskBadge');

        const isApproved = data.prediction === 1;

        if (isApproved) {
            decisionBox.className = 'decision-box approved';
            decisionTitle.textContent = '✅ Prediction: Likely Approved';
            decisionSub.textContent = 'The ML classification model estimates this application is likely to meet lending approval criteria.';
        } else {
            decisionBox.className = 'decision-box rejected';
            decisionTitle.textContent = '❌ Prediction: Likely Not Approved';
            decisionSub.textContent = 'The ML classification model estimates this application poses high default or credit risk.';
        }

        riskBadge.textContent = data.risk_level;

        // Animate Probability Meters
        const appProb = data.approval_probability;
        const rejProb = data.rejection_probability;

        document.getElementById('approvalProbText').textContent = `${appProb.toFixed(1)}%`;
        document.getElementById('rejectionProbText').textContent = `${rejProb.toFixed(1)}%`;

        document.getElementById('approvalProbBar').style.width = `${appProb}%`;
        document.getElementById('rejectionProbBar').style.width = `${rejProb}%`;

        // Explanatory Factors
        const factorsList = document.getElementById('factorsList');
        factorsList.innerHTML = '';
        if (data.key_factors && data.key_factors.length > 0) {
            data.key_factors.forEach(factor => {
                const li = document.createElement('li');
                li.innerHTML = `📌 ${factor}`;
                factorsList.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = 'Standard risk profile based on financial criteria.';
            factorsList.appendChild(li);
        }

        // Disclaimer
        document.getElementById('disclaimerText').textContent = data.disclaimer;

    } catch (error) {
        alert('Error communicating with prediction server: ' + error.message);
    } finally {
        submitBtn.innerHTML = originalBtnText;
        submitBtn.disabled = false;
    }
}
