let chart;

async function plotGraph() {
  const exprInput = document.getElementById('expression').value;
  const expressions = exprInput.split(',').map(e => e.trim());
  const xMin = parseFloat(document.getElementById('xMin').value);
  const xMax = parseFloat(document.getElementById('xMax').value);
  const res = await fetch('/plot', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({expressions, xMin, xMax})
  });
  const data = await res.json();
  drawChart(data.x, data.ySets);
}

function drawChart(x, ySets) {
  const ctx = document.getElementById('chart').getContext('2d');
  if (chart) chart.destroy();
  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: x,
      datasets: ySets.map((ys, i) => ({
        label: ys.expr,
        data: ys.values,
        borderColor: ['red','blue','green','orange','purple'][i % 5],
        fill: false
      }))
    },
    options: {responsive: true, scales: {x: {title: {display: true, text: 'x'}}, y: {title: {display: true, text: 'y'}}}}
  });
}

async function showDerivative() {
  const expr = document.getElementById('expression').value.split(',')[0];
  const res = await fetch('/derivative', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({expression: expr})
  });
  const data = await res.json();
  drawChart(data.x, [{expr: 'f'(x)', values: data.y}]);
  document.getElementById('result').innerHTML = '<b>Turunan fungsi pertama ditampilkan.</b>';
}

async function showIntegral() {
  const expr = document.getElementById('expression').value.split(',')[0];
  const a = parseFloat(prompt('Masukkan batas bawah a:', '0'));
  const b = parseFloat(prompt('Masukkan batas atas b:', '5'));
  const res = await fetch('/integral', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({expression: expr, a, b})
  });
  const data = await res.json();
  drawChart(data.x, [{expr: expr, values: data.y}]);
  document.getElementById('result').innerHTML = `Luas area (integral) ≈ <b>${data.area.toFixed(4)}</b>`;
}

async function saveProgress() {
  const expr = document.getElementById('expression').value;
  const progress = {expr, time: new Date().toLocaleString()};
  await fetch('/save', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(progress)
  });
  alert('Progress tersimpan!');
}
