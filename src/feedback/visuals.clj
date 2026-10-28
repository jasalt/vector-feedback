(ns feedback.visuals
  (:require [clojure.string :as str]
            [feedback.model :as model]))

;; One immutable Slipstream vector quad. Only uniforms change: no per-frame
;; path tessellation, atlas allocation, or GPU readback. Each inverse matrix
;; projects a pixel back onto a surviving vector frame.
(def fragment
  (str
    "float segment(vec2 p, vec2 a, vec2 b) {
       vec2 q=p-a, v=b-a;
       return length(q-v*clamp(dot(q,v)/dot(v,v),0.0,1.0));
     }
     float ink(vec3 q) {
       if(q.z <= 0.000001) return 0.0;
       vec2 p=q.xy/q.z;
       vec2 edge=abs(abs(p)-vec2(1.18,0.68));
       float d=min(max(edge.x,abs(p.y)-0.68),max(edge.y,abs(p.x)-1.18));
       d=min(d,segment(p,vec2(-0.12,0),vec2(0.12,0)));
       d=min(d,segment(p,vec2(0,-0.12),vec2(0,0.12)));
       float aa=max(length(fwidth(p)),0.0001);
       return 1.0-smoothstep(0.0015,0.0015+aa,d);
     }
     vec4 slipstream_fragment(vec4 color,float fill,float sd,vec2 p,float effectParam) {
       vec3 light=vec3(0.0);
       vec3 point=vec3(p-vec2(1.6,1.0),1.0);
       float a=0.0;
       vec3 tint=vec3(0.0);
"
    (str/join "\n"
      (for [i (range model/depth)]
        (str "a=ink(u_frame" i "*point)*pow(u_decay," (double i) ");\n"
             "tint=0.55+0.45*cos(vec3(0.0,2.1,4.2)+" (* i 0.13) "+u_time*0.12);\n"
             "light+=a*tint*0.72;")))
    "
       vec3 background=vec3(0.006,0.012,0.024);
       vec3 rgb=background+(1.0-exp(-light*1.7));
       return vec4(rgb,1.0);
     }"))

(defn column-major [m]
  (mapv #(nth m %) [0 3 6 1 4 7 2 5 8]))
(def hidden-matrix [0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 -1.0])
(defn effect [{:keys [history camera time]}]
  {:id 1 :fragment-hook fragment
   :uniforms
   (into {:decay {:type :float :value (:decay camera)}
          :time {:type :float :value time}}
         (for [i (range model/depth)]
           [(keyword (str "frame" i))
            {:type :mat3
             :value (column-major
                      (or (when (< i (count history)) (model/inverse (nth history i)))
                          hidden-matrix))}]))})
(defn label [font text at size color]
  [:text {:font font :text text :at at :size size :color color
          :align :left :anchor :baseline}])
(defn scene [state font]
  (let [c (:camera state)]
    [:scene {}
     [:shape {:path [[:rect 0 0 3.2 2.0]] :at [-1.6 -1.0 0] :fill [1 1 1 1]
              :effect (effect state)}]
     (label font "PICTURE PLANE / VECTOR FEEDBACK" [-1.49 0.88 0] 0.052 [0.65 0.84 0.95 1])
     (label font (if (:paused state) "PAUSED" "LIVE / 30 Hz") [1.03 0.88 0] 0.041 [0.35 1 0.75 1])
     [:shape {:path [[:rect 0 0 3.2 0.23]] :at [-1.6 -1.0 0] :fill [0.008 0.018 0.03 0.97]}]
     (label font "LEFT DRAG pan   RIGHT DRAG yaw/pitch   MIDDLE DRAG roll   WHEEL dolly" [-1.49 -0.855 0] 0.037 [0.75 0.85 0.9 1])
     (label font (format "SPACE pause   R reset     zoom %.3f   roll %.1f   yaw %.1f   pitch %.1f"
                        (:zoom c) (* 57.2958 (:roll c)) (* 57.2958 (:yaw c)) (* 57.2958 (:pitch c)))
            [-1.49 -0.935 0] 0.035 [0.4 0.6 0.7 1])]))
