if (module.hot) {
    module.hot.accept();
}

var DEBUG = false
const Application = require('./application')
const planck = require('planck-js')

Application((app) => {
    var pl = planck, Vec2 = pl.Vec2;

    var COLORS = [
        { fill: '#008000', stroke: '#000000' },
        { fill: '#ffdd00', stroke: '#ffffff' },
        { fill: '#ff0000', stroke: '#ffffff' },
    ];

    var width = 12.0, height = 6.00;

    var BALL_R = 0.25;
    var RAIL_W = 0.2;
    var POCKET_L = height / 3;

    app.x = 0;
    app.y = 0;
    app.width = width * 1.2;
    app.height = height * 1.2;
    app.mouseRestrictions = {
        xMin: (-width + BALL_R) / 2,
        xMax: (width - BALL_R) / 2,
        yMin: (-height + BALL_R) / 2,
        yMax: (height - BALL_R) / 2,
    }
    app.ratio = 100;
    app.mouseForce = 30;

    pl.internal.Settings.velocityThreshold = 0;

    var world = pl.World({});

    var railH = [
        Vec2(-width * .5, height * .5),
        Vec2(width * .5, height * .5 + RAIL_W),
        Vec2(-width * .5, height * .5 + RAIL_W),
        Vec2(width * .5, height * .5)
    ];

    var railV = [
        Vec2(width * .5, POCKET_L * .5),
        Vec2(width * .5, height * .5),
        Vec2(width * .5 + RAIL_W, height * .5),
        Vec2(width * .5 + RAIL_W, POCKET_L * .5),
    ];

    var pocketV = [
        Vec2(width * .5 + RAIL_W, -POCKET_L * .5),
        Vec2(width * .5 + RAIL_W, POCKET_L * .5),
        Vec2(width * .5 + 2 * RAIL_W, POCKET_L * .5),
        Vec2(width * .5 + 2 * RAIL_W, -POCKET_L * .5),
    ];

    var railFixDef = {
        friction: 0.1,
        restitution: 0.9,
        userData: 'rail'
    };
    var pocketFixDef = {
        userData: 'pocket'
    };
    var ballFixDef = {
        friction: 0.1,
        restitution: 0.99,
        density: 0.5,
        userData: 'ball'
    };
    var ballBodyDef = {
        linearDamping: 0.9,
        angularDamping: 1
    };

    var pusherFixDef = {
        friction: 0.1,
        restitution: 0.99,
        density: 0.5,
        userData: 'pusher'
    };

    const markerRender = { fill: '#00fff0', stroke: '#00ffff' }

    const marker1 = world.createKinematicBody(Vec2(-2, 3 + RAIL_W / 2), 0)
    marker1.createFixture(pl.Circle(RAIL_W / 2), {});
    marker1.render = markerRender

    const marker2 = world.createKinematicBody(Vec2(-2, -3 - RAIL_W / 2), 0)
    marker2.createFixture(pl.Circle(RAIL_W / 2), {});
    marker2.render = markerRender


    world.createBody().createFixture(pl.Polygon(railV.map(Vec2.scaleFn(+1, +1))), railFixDef);
    world.createBody().createFixture(pl.Polygon(railV.map(Vec2.scaleFn(-1, +1))), railFixDef);
    world.createBody().createFixture(pl.Polygon(railV.map(Vec2.scaleFn(+1, -1))), railFixDef);
    world.createBody().createFixture(pl.Polygon(railV.map(Vec2.scaleFn(-1, -1))), railFixDef);

    world.createBody().createFixture(pl.Polygon(pocketV.map(Vec2.scaleFn(-1, 1))), pocketFixDef);
    world.createBody().createFixture(pl.Polygon(pocketV.map(Vec2.scaleFn(+1, 1))), pocketFixDef);

    world.createBody().createFixture(pl.Polygon(railH.map(Vec2.scaleFn(+1, +1))), railFixDef);
    world.createBody().createFixture(pl.Polygon(railH.map(Vec2.scaleFn(-1, -1))), railFixDef);


    var pusher = world.createDynamicBody(ballBodyDef);
    pusher.createFixture(pl.Circle(BALL_R), pusherFixDef);

    var aiPusher = world.createDynamicBody(ballBodyDef);
    aiPusher.createFixture(pl.Circle(BALL_R), pusherFixDef);
    aiPusher.render = COLORS[1];
    aiPusher.setPosition({ x: -width / 6, y: 0 });

    var balls = [];
    balls.push({ x: -width / 4, y: 0, render: COLORS[0] });
    // balls.push({x: -width / 5, y: 0, render: COLORS[1]});

    for (i = 0; i < balls.length; i++) {
        var ball = world.createDynamicBody(ballBodyDef);
        ball.setBullet(true);
        ball.setPosition(balls[i]);
        ball.createFixture(pl.Circle(BALL_R), ballFixDef);
        ball.render = balls[i].render;
    }

    const aiPusherGround = world.createBody();
    const aiPusherJoint = planck.MouseJoint({
        maxForce: 100,
        dampingRatio: 5,
        frequencyHz: 10,
        collideConnected: true,
    }, aiPusherGround, aiPusher, aiPusher.getPosition());
    world.createJoint(aiPusherJoint);

    // var connection = new WebSocket('ws://localhost:1122');
    window.api.UdpCallback((event, value) => {
        console.log('test')
        console.log(value)
        aiPusherJoint.setTarget(JSON.parse(value));
    })
    // connection.onmessage = function (e) {
    //     console.log(e);
    //     if (e.data == 'ping') {
    //         console.log('received ping message')
    //         connection.send('pong airhockey');
    //         return;
    //     }

    //     aiPusherJoint.setTarget(JSON.parse(e.data));
    // };


    world.on('post-solve', function (contact) {
        var fA = contact.getFixtureA(), bA = fA.getBody();
        var fB = contact.getFixtureB(), bB = fB.getBody();

        var pocket = fA.getUserData() === pocketFixDef.userData && bA || fB.getUserData() === pocketFixDef.userData && bB;
        var ball = fA.getUserData() === ballFixDef.userData && bA || fB.getUserData() === ballFixDef.userData && bB;

        // do not change world immediately
        setTimeout(function () {
            if (ball && pocket) {
                //        world.destroyBody(ball);
            }
        }, 1);
    });

    return [world, pusher];
});