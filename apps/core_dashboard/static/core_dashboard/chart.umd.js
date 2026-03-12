/* Minimal Chart.js-compatible wrapper for dashboard usage. */
(function () {
  function drawBar(ctx, labels, values) {
    var width = ctx.canvas.width;
    var height = ctx.canvas.height;
    ctx.clearRect(0, 0, width, height);
    var max = Math.max.apply(null, values.concat([1]));
    var barWidth = width / Math.max(labels.length, 1);
    for (var i = 0; i < values.length; i++) {
      var h = (values[i] / max) * (height - 20);
      ctx.fillStyle = "#0d6efd";
      ctx.fillRect(i * barWidth + 10, height - h - 10, barWidth - 20, h);
    }
  }

  function drawDoughnut(ctx, values) {
    var width = ctx.canvas.width;
    var height = ctx.canvas.height;
    var total = values.reduce(function (a, b) { return a + b; }, 0) || 1;
    var cx = width / 2;
    var cy = height / 2;
    var r = Math.min(width, height) / 2 - 10;
    var start = 0;
    var colors = ["#198754", "#dc3545", "#ffc107"];
    for (var i = 0; i < values.length; i++) {
      var slice = (values[i] / total) * Math.PI * 2;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.fillStyle = colors[i % colors.length];
      ctx.arc(cx, cy, r, start, start + slice);
      ctx.closePath();
      ctx.fill();
      start += slice;
    }
    ctx.globalCompositeOperation = "destination-out";
    ctx.beginPath();
    ctx.arc(cx, cy, r * 0.55, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalCompositeOperation = "source-over";
  }

  function Chart(ctx, config) {
    this.ctx = ctx;
    this.config = config || {};
    this.render();
  }

  Chart.prototype.render = function () {
    var data = (this.config && this.config.data) || {};
    var labels = data.labels || [];
    var values = (data.datasets && data.datasets[0] && data.datasets[0].data) || [];
    if (this.config.type === "bar") {
      drawBar(this.ctx, labels, values);
      return;
    }
    if (this.config.type === "doughnut") {
      drawDoughnut(this.ctx, values);
      return;
    }
  };

  window.Chart = Chart;
})();
