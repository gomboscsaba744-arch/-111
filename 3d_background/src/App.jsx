import * as THREE from 'three';
import { useRef, useMemo, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';

function Strands() {
  const materialRef = useRef();

  const uniforms = useMemo(() => ({
    uTime: { value: 0 },
    uColor1: { value: new THREE.Color('#ff7e67') }, // Orange
    uColor2: { value: new THREE.Color('#a960ee') }, // Purple
    uColor3: { value: new THREE.Color('#90e0ef') }, // Cyan
    uThickness: { value: 0.131 },
    uBlur: { value: 0.12 },
    uBrightness: { value: 0.8 },
  }), []);

  useEffect(() => {
    const handleMessage = (e) => {
      if (e.data?.type === 'UPDATE_STRANDS') {
        const { thickness, blur, brightness } = e.data.payload;
        if (materialRef.current) {
          materialRef.current.uniforms.uThickness.value = thickness;
          materialRef.current.uniforms.uBlur.value = blur;
          materialRef.current.uniforms.uBrightness.value = brightness;
        }
      }
    };
    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  const vertexShader = `
    varying vec2 vUv;
    void main() {
      vUv = uv;
      // Make the plane cover the entire screen
      gl_Position = vec4(position.x, position.y, 0.0, 1.0);
    }
  `;

  const fragmentShader = `
    uniform float uTime;
    uniform vec3 uColor1;
    uniform vec3 uColor2;
    uniform vec3 uColor3;
    uniform float uThickness;
    uniform float uBlur;
    uniform float uBrightness;
    varying vec2 vUv;

    void main() {
      // Map uv to [-1, 1]
      vec2 uv = vUv * 2.0 - 1.0;
      
      // We want to stretch the x axis slightly
      uv.x *= 1.2;
      
      vec3 finalColor = vec3(0.0);
      
      // Create 3 glowing strands
      for(float i = 1.0; i <= 3.0; i++) {
        // Wider envelope so it extends beyond the screen edges
        float env = smoothstep(1.6, 0.0, abs(uv.x)); 
        
        // Multi-frequency wave - longer wavelength
        float wave = sin(uv.x * 2.0 + uTime * (0.2 + i * 0.08)) * 0.6; 
        wave *= sin(uTime * 0.2 + i * 1.2) * 0.8 + 0.2; // Modulate amplitude
        // Do not pinch to zero at edges! Keep 30% amplitude so it flows from off-screen
        wave *= mix(0.3, 1.0, env); 
        
        // Distance field for glow controlled by live uniforms
        float dist = abs(uv.y - wave);
        float strand = uThickness / (dist + uBlur); 
        
        // Color mix
        vec3 color = uColor1;
        if(i == 2.0) color = uColor2;
        if(i == 3.0) color = uColor3;
        
        // Brightness balance
        finalColor += color * strand * mix(0.5, 1.0, env) * uBrightness; 
      }
      
      // The background should be completely transparent so Streamlit shows through,
      // but the glowing lines should have alpha based on their brightness.
      float alpha = max(max(finalColor.r, finalColor.g), finalColor.b);
      
      gl_FragColor = vec4(finalColor, alpha);
    }
  `;

  useFrame((state) => {
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = state.clock.elapsedTime;
    }
  });

  return (
    <mesh>
      <planeGeometry args={[2, 2]} />
      <shaderMaterial
        ref={materialRef}
        vertexShader={vertexShader}
        fragmentShader={fragmentShader}
        uniforms={uniforms}
        transparent={true}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </mesh>
  );
}

export default function App() {
  return (
    <div style={{ width: '100vw', height: '100vh', background: 'transparent' }}>
      <Canvas gl={{ alpha: true, antialias: true }} camera={{ position: [0, 0, 1] }}>
        <Strands />
      </Canvas>
    </div>
  );
}
