DEBUG = false;
const Stage = require('stage-js/platform/web')
const Viewer = require('./viewer')
const planck = require('planck-js')

const Application = function(callback) {
  Stage(function(stage, canvas) {

    stage.on(Stage.Mouse.START, function() {
      window.focus();
      document.activeElement && document.activeElement.blur();
      canvas.focus();
    });

    stage.MAX_ELAPSE = 1000 / 30;
    var Vec2 = planck.Vec2;

    var app = {};
    app.canvas = canvas;
    app.debug = false;
    app.width = 80;
    app.height = 60;
    app.mouseRestrictions = {
      xMin: -app.width / 2,
      xMax: app.width / 2,
      yMin: app.height / 2,
      yMax: app.height / 2,
    }
    app.x = 0;
    app.y = -10;
    app.scaleY = -1;
    app.ratio = 16;
    app.hz = 60;
    app.speed = 1;
    app.activeKeys = {};
    app.background = '#222222';

    var lastDrawHash = "", drawHash = "";


    var [world, mouseBody] = callback(app);

    var viewer = new Viewer(world, app);

    var lastX = 0, lastY = 0;
    stage.tick(function(dt, t) {
      // update camera position
      if (lastX !== app.x || lastY !== app.y) {
        viewer.offset(-app.x, -app.y);
        lastX = app.x, lastY = app.y;
      }
    });

    viewer.tick(function(dt, t) {
      // call app step, if provided
      if (typeof app.step === 'function') {
        app.step(dt, t);
      }

      if (lastDrawHash !== drawHash) {
        lastDrawHash = drawHash;
        stage.touch();
      }
      drawHash = "";

      return true;
    });

    // stage.empty();
    stage.background(app.background);
    stage.viewbox(app.width, app.height);
    stage.pin('alignX', -0.5);
    stage.pin('alignY', -0.5);
    stage.prepend(viewer);

    const mouseGround = world.createBody();
    const mouseJoint = planck.MouseJoint({
      maxForce: 1000,
      dampingRatio: 1,
      frequencyHz: 1000
    }, mouseGround, mouseBody, Vec2({x: 0, y: 0}));
    world.createJoint(mouseJoint);

    viewer.attr('spy', true).on(Stage.Mouse.MOVE, function(point) {
      point = { x: point.x, y: app.scaleY * point.y };
      const r = app.mouseRestrictions;
      if (point.x < r.xMin) {
        point.x = r.xMin;
      }

      if (point.x > r.xMax) {
        point.x = r.xMax;
      }

      if (point.y < r.yMin) {
        point.y = r.yMin;
      }

      if (point.y > r.yMax) {
        point.y = r.yMax;
      }

      if (mouseJoint) {
        mouseJoint.setTarget(point);
      }

    })
  });
};

module.exports = Application;