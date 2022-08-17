const Stage = require('stage-js/platform/web')

Viewer._super = Stage;
Viewer.prototype = Stage._create(Viewer._super.prototype);

function Viewer(world, opts) {
    Viewer._super.call(this);
    this.label('Planck');

    opts = opts || {};

    var options = this._options = {};
    this._options.speed = opts.speed || 1;
    this._options.hz = opts.hz || 60;
    if (Math.abs(this._options.hz) < 1) {
        this._options.hz = 1 / this._options.hz;
    }
    this._options.scaleY = opts.scaleY || -1;
    this._options.ratio = opts.ratio || 16;
    this._options.lineWidth = 2 / this._options.ratio;

    this._world = world;

    var timeStep = 1 / this._options.hz;
    var elapsedTime = 0;
    this.tick(function (dt) {
        dt = dt * 0.001 * options.speed;
        elapsedTime += dt;
        while (elapsedTime > timeStep) {
            world.step(timeStep);
            elapsedTime -= timeStep;
        }
        this.renderWorld();
        return true;
    }, true);

    world.on('remove-fixture', function (obj) {
        obj.ui && obj.ui.remove();
    });

    world.on('remove-joint', function (obj) {
        obj.ui && obj.ui.remove();
    });
}

Viewer.prototype.renderWorld = function (world) {
    var world = this._world;
    var options = this._options;
    var viewer = this;

    for (var b = world.getBodyList(); b; b = b.getNext()) {
        for (var f = b.getFixtureList(); f; f = f.getNext()) {

            if (!f.ui) {
                if (f.render && f.render.stroke) {
                    options.strokeStyle = f.render.stroke;
                } else if (b.render && b.render.stroke) {
                    options.strokeStyle = b.render.stroke;
                } else if (b.isDynamic()) {
                    options.strokeStyle = 'rgba(255,255,255,0.9)';
                } else if (b.isKinematic()) {
                    options.strokeStyle = 'rgba(255,255,255,0.7)';
                } else if (b.isStatic()) {
                    options.strokeStyle = 'rgba(255,255,255,0.5)';
                }

                if (f.render && f.render.fill) {
                    options.fillStyle = f.render.fill;
                } else if (b.render && b.render.fill) {
                    options.fillStyle = b.render.fill;
                } else {
                    options.fillStyle = '';
                }

                var type = f.getType();
                var shape = f.getShape();
                if (type == 'circle') {
                    f.ui = viewer.drawCircle(shape, options);
                }
                if (type == 'edge') {
                    f.ui = viewer.drawEdge(shape, options);
                }
                if (type == 'polygon') {
                    f.ui = viewer.drawPolygon(shape, options);
                }
                if (type == 'chain') {
                    f.ui = viewer.drawChain(shape, options);
                }

                if (f.ui) {
                    f.ui.appendTo(viewer);
                }
            }

            if (f.ui) {
                var p = b.getPosition(), r = b.getAngle();
                if (f.ui.__lastX !== p.x || f.ui.__lastY !== p.y || f.ui.__lastR !== r) {
                    f.ui.__lastX = p.x;
                    f.ui.__lastY = p.y;
                    f.ui.__lastR = r;
                    f.ui.offset(p.x, options.scaleY * p.y);
                    f.ui.rotate(options.scaleY * r);
                }
            }

        }
    }

    for (var j = world.getJointList(); j; j = j.getNext()) {
        var type = j.getType();
        var a = j.getAnchorA();
        var b = j.getAnchorB();

        if (!j.ui) {
            options.strokeStyle = 'rgba(255,255,255,0.2)';

            j.ui = viewer.drawJoint(j, options);
            j.ui.pin('handle', 0.5);
            if (j.ui) {
                j.ui.appendTo(viewer);
            }
        }

        if (j.ui) {
            var cx = (a.x + b.x) * 0.5;
            var cy = options.scaleY * (a.y + b.y) * 0.5;
            var dx = a.x - b.x;
            var dy = options.scaleY * (a.y - b.y);
            var d = Math.sqrt(dx * dx + dy * dy);
            j.ui.width(d);
            j.ui.rotate(Math.atan2(dy, dx));
            j.ui.offset(cx, cy);
        }
    }

}

Viewer.prototype.drawJoint = function (joint, options) {
    var lw = options.lineWidth;
    var ratio = options.ratio;

    var length = 10;

    var texture = Stage.canvas(function (ctx) {

        this.size(length + 2 * lw, 2 * lw, ratio);

        ctx.scale(ratio, ratio);
        ctx.beginPath();
        ctx.moveTo(lw, lw);
        ctx.lineTo(lw + length, lw);

        ctx.lineCap = 'round';
        ctx.lineWidth = options.lineWidth;
        ctx.strokeStyle = options.strokeStyle;
        ctx.stroke();
    });

    var image = Stage.image(texture).stretch();
    return image;
};

Viewer.prototype.drawCircle = function (shape, options) {
    var lw = options.lineWidth;
    var ratio = options.ratio;

    var r = shape.m_radius;
    var cx = r + lw;
    var cy = r + lw;
    var w = r * 2 + lw * 2;
    var h = r * 2 + lw * 2;

    var texture = Stage.canvas(function (ctx) {

        this.size(w, h, ratio);

        ctx.scale(ratio, ratio);
        ctx.arc(cx, cy, r, 0, 2 * Math.PI);
        if (options.fillStyle) {
            ctx.fillStyle = options.fillStyle;
            ctx.fill();
        }
        ctx.lineTo(cx, cy);
        ctx.lineWidth = options.lineWidth;
        ctx.strokeStyle = options.strokeStyle;
        ctx.stroke();
    });
    var image = Stage.image(texture)
        .offset(shape.m_p.x - cx, options.scaleY * shape.m_p.y - cy);
    var node = Stage.create().append(image);
    return node;
};

Viewer.prototype.drawEdge = function (edge, options) {
    var lw = options.lineWidth;
    var ratio = options.ratio;

    var v1 = edge.m_vertex1;
    var v2 = edge.m_vertex2;

    var dx = v2.x - v1.x;
    var dy = v2.y - v1.y;

    var length = Math.sqrt(dx * dx + dy * dy);

    var texture = Stage.canvas(function (ctx) {

        this.size(length + 2 * lw, 2 * lw, ratio);

        ctx.scale(ratio, ratio);
        ctx.beginPath();
        ctx.moveTo(lw, lw);
        ctx.lineTo(lw + length, lw);

        ctx.lineCap = 'round';
        ctx.lineWidth = options.lineWidth;
        ctx.strokeStyle = options.strokeStyle;
        ctx.stroke();
    });

    var minX = Math.min(v1.x, v2.x);
    var minY = Math.min(options.scaleY * v1.y, options.scaleY * v2.y);

    var image = Stage.image(texture);
    image.rotate(options.scaleY * Math.atan2(dy, dx));
    image.offset(minX - lw, minY - lw);
    var node = Stage.create().append(image);
    return node;
};

Viewer.prototype.drawPolygon = function (shape, options) {
    var lw = options.lineWidth;
    var ratio = options.ratio;

    var vertices = shape.m_vertices;

    if (!vertices.length) {
        return;
    }

    var minX = Infinity, minY = Infinity;
    var maxX = -Infinity, maxY = -Infinity;
    for (var i = 0; i < vertices.length; ++i) {
        var v = vertices[i];
        minX = Math.min(minX, v.x);
        maxX = Math.max(maxX, v.x);
        minY = Math.min(minY, options.scaleY * v.y);
        maxY = Math.max(maxY, options.scaleY * v.y);
    }

    var width = maxX - minX;
    var height = maxY - minY;

    var texture = Stage.canvas(function (ctx) {

        this.size(width + 2 * lw, height + 2 * lw, ratio);

        ctx.scale(ratio, ratio);
        ctx.beginPath();
        for (var i = 0; i < vertices.length; ++i) {
            var v = vertices[i];
            var x = v.x - minX + lw;
            var y = options.scaleY * v.y - minY + lw;
            if (i == 0)
                ctx.moveTo(x, y);
            else
                ctx.lineTo(x, y);
        }

        if (vertices.length > 2) {
            ctx.closePath();
        }

        if (options.fillStyle) {
            ctx.fillStyle = options.fillStyle;
            ctx.fill();
            ctx.closePath();
        }

        ctx.lineCap = 'round';
        ctx.lineWidth = options.lineWidth;
        ctx.strokeStyle = options.strokeStyle;
        ctx.stroke();
    });

    var image = Stage.image(texture);
    image.offset(minX - lw, minY - lw);
    var node = Stage.create().append(image);
    return node;
};

Viewer.prototype.drawChain = function (shape, options) {
    var lw = options.lineWidth;
    var ratio = options.ratio;

    var vertices = shape.m_vertices;

    if (!vertices.length) {
        return;
    }

    var minX = Infinity, minY = Infinity;
    var maxX = -Infinity, maxY = -Infinity;
    for (var i = 0; i < vertices.length; ++i) {
        var v = vertices[i];
        minX = Math.min(minX, v.x);
        maxX = Math.max(maxX, v.x);
        minY = Math.min(minY, options.scaleY * v.y);
        maxY = Math.max(maxY, options.scaleY * v.y);
    }

    var width = maxX - minX;
    var height = maxY - minY;

    var texture = Stage.canvas(function (ctx) {

        this.size(width + 2 * lw, height + 2 * lw, ratio);

        ctx.scale(ratio, ratio);
        ctx.beginPath();
        for (var i = 0; i < vertices.length; ++i) {
            var v = vertices[i];
            var x = v.x - minX + lw;
            var y = options.scaleY * v.y - minY + lw;
            if (i == 0)
                ctx.moveTo(x, y);
            else
                ctx.lineTo(x, y);
        }

        // TODO: if loop
        if (vertices.length > 2) {
            // ctx.closePath();
        }

        if (options.fillStyle) {
            ctx.fillStyle = options.fillStyle;
            ctx.fill();
            ctx.closePath();
        }

        ctx.lineCap = 'round';
        ctx.lineWidth = options.lineWidth;
        ctx.strokeStyle = options.strokeStyle;
        ctx.stroke();
    });

    var image = Stage.image(texture);
    image.offset(minX - lw, minY - lw);
    var node = Stage.create().append(image);
    return node;
};

module.exports = Viewer