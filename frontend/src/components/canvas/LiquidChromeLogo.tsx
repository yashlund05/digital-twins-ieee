import React, { useEffect, useRef } from 'react';

export interface LiquidChromeLogoProps {
  size?: number;
  className?: string;
}

/**
 * LiquidChromeLogo
 * Real-time WebGL simplex noise shader simulation morphing the digital twin insignia
 * into reflective liquid chrome metal. Ported from collidingScopes/liquid-logo.
 */
export const LiquidChromeLogo: React.FC<LiquidChromeLogoProps> = ({
  size = 180,
  className = '',
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const gl = canvas.getContext('webgl');
    if (!gl) return;

    const vs = `
      attribute vec2 a_position;
      varying vec2 v_uv;
      void main() {
        v_uv = (a_position + 1.0) * 0.5;
        v_uv.y = 1.0 - v_uv.y;
        gl_Position = vec4(a_position, 0.0, 1.0);
      }
    `;

    const fs = `
      precision highp float;
      varying vec2 v_uv;
      uniform float u_time;

      vec2 hash(vec2 p) {
        p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)));
        return -1.0 + 2.0 * fract(sin(p) * 43758.5453123);
      }

      float noise(vec2 p) {
        vec2 i = floor(p);
        vec2 f = fract(p);
        vec2 u = f * f * (3.0 - 2.0 * f);
        return mix(mix(dot(hash(i + vec2(0.0, 0.0)), f - vec2(0.0, 0.0)),
                       dot(hash(i + vec2(1.0, 0.0)), f - vec2(1.0, 0.0)), u.x),
                   mix(dot(hash(i + vec2(0.0, 1.0)), f - vec2(0.0, 1.0)),
                       dot(hash(i + vec2(1.0, 1.0)), f - vec2(1.0, 1.0)), u.x), u.y);
      }

      void main() {
        vec2 uv = v_uv - 0.5;
        float dist = length(uv);
        float angle = atan(uv.y, uv.x);
        float t = u_time * 0.8;

        // Fluid distortion waves
        float n1 = noise(uv * 7.0 + vec2(t * 0.6, -t * 0.4));
        float n2 = noise(uv * 12.0 - vec2(-t * 0.5, t * 0.7));
        float wave = n1 * 0.6 + n2 * 0.4;

        // Procedural Twin Ring Emblem
        float ring1 = smoothstep(0.04, 0.0, abs(dist - 0.28 + wave * 0.04));
        float ring2 = smoothstep(0.03, 0.0, abs(dist - 0.16 + wave * 0.03));
        float core = smoothstep(0.08, 0.02, dist);

        // Liquid chrome specular reflection highlight
        float specular = pow(max(0.0, sin(angle * 2.0 + wave * 4.0 + t)), 4.0);

        // Chrome color gradients (Electric Cyan / Specular Platinum / Deep Slate)
        vec3 chrome = vec3(0.85, 0.92, 1.0); // Base platinum
        chrome += vec3(0.0, 0.6, 0.9) * specular; // Cyan sheen
        chrome += vec3(specular * 0.8); // Specular white rim

        float alpha = clamp(ring1 + ring2 + core * 0.7, 0.0, 1.0);
        gl_FragColor = vec4(chrome * alpha, alpha);
      }
    `;

    function compile(type: number, src: string) {
      const s = gl!.createShader(type)!;
      gl!.shaderSource(s, src);
      gl!.compileShader(s);
      return s;
    }

    const prog = gl.createProgram()!;
    gl.attachShader(prog, compile(gl.VERTEX_SHADER, vs));
    gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(prog);
    gl.useProgram(prog);

    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(
      gl.ARRAY_BUFFER,
      new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]),
      gl.STATIC_DRAW
    );

    const aPos = gl.getAttribLocation(prog, 'a_position');
    gl.enableVertexAttribArray(aPos);
    gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);

    const uTime = gl.getUniformLocation(prog, 'u_time');

    let animId: number;
    const startTime = performance.now();

    const render = () => {
      const elapsed = (performance.now() - startTime) / 1000;
      gl.viewport(0, 0, size, size);
      gl.uniform1f(uTime, elapsed);
      gl.drawArrays(gl.TRIANGLES, 0, 6);
      animId = requestAnimationFrame(render);
    };
    render();

    return () => {
      cancelAnimationFrame(animId);
      gl.deleteProgram(prog);
      gl.deleteBuffer(buf);
    };
  }, [size]);

  return (
    <div className={`relative flex items-center justify-center ${className}`}>
      <div className="absolute inset-0 rounded-full bg-cyan-500/20 blur-xl pointer-events-none" />
      <canvas
        ref={canvasRef}
        width={size}
        height={size}
        className="relative z-10 rounded-full"
      />
    </div>
  );
};

export default LiquidChromeLogo;
