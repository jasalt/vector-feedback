(ns witness
  "Reduced real Slipstream ABI gate, independent of GL and Glimmer."
  (:require [jolt.ffi :as ffi]))

(ffi/defcfn atlas-new "ss_atlas_new" [:uint32 :int32] :pointer)
(ffi/defcfn atlas-destroy "ss_atlas_destroy" [:pointer] :int32)
(ffi/defcfn atlas-build "ss_atlas_build" [:pointer] :int32)
(ffi/defcfn atlas-built? "ss_atlas_is_built" [:pointer] :bool)
(ffi/defcfn path-new "ss_path_new" [] :pointer)
(ffi/defcfn path-destroy "ss_path_destroy" [:pointer] :int32)
(ffi/defcfn raw-path-command "ss_path_command" [:pointer :uint32 :pointer :uint64] :int32)
(ffi/defcfn path-command "web_path_command" [:pointer :uint32 :pointer :uint32] :int32)
(ffi/defcfn u64-low "web_u64_low" [:uint64] :int32)
(ffi/defcfn u64-high "web_u64_high" [:uint64] :int32)
(ffi/defcfn canvas-new "ss_canvas_new" [:pointer :uint32] :pointer)
(ffi/defcfn canvas-destroy "ss_canvas_destroy" [:pointer] :int32)
(ffi/defcfn read-float "web_read_float" [:pointer] :int32)
(ffi/defcfn define-shape "web_define_shape"
  [:pointer :pointer :pointer :float :uint32 :float :float] :int32)
(ffi/defcfn define-shape-p "web_define_shape_p" [:pointer :pointer :pointer :pointer] :int32)
(ffi/defcfn shape-quad-p "web_shape_quad_p" [:pointer :pointer :pointer :pointer] :int32)
(ffi/defcfn get-shape "ss_atlas_get_shape" [:pointer :pointer :pointer] :int32)
(ffi/defcfn shape-quad "ss_shape_quad" [:pointer :pointer :float :pointer] :int32)
(ffi/defcfn last-error "ss_last_error" [] :string)

(def key-layout (ffi/layout [:struct [[:type :uint32] [:codepoint :uint32] [:name :pointer]]]))
(def shape-layout
  (ffi/layout [:struct [[:band-tex-x :uint32] [:band-tex-y :uint32]
                       [:band-max-x :uint32] [:band-max-y :uint32]
                       [:band-scale-x :float] [:band-scale-y :float]
                       [:band-offset-x :float] [:band-offset-y :float]
                       [:bearing-x :float] [:bearing-y :float]
                       [:width :float] [:height :float] [:advance :float]
                       [:origin-x :float] [:origin-y :float]
                       [:origin-type :uint32] [:origin-data-x :float] [:origin-data-y :float]]]))
(defn check [truth label]
  (when-not truth (throw (ex-info (str "ABI failure: " label " / " (last-error)) {}))))
(defn near? [x y] (< (Math/abs (- (double x) (double y))) 0.0001))
(defn -main [& args]
  (let [atlas (atlas-new 1024 32)
        path (path-new)
        canvas (canvas-new atlas 1000)
        rect (ffi/alloc 16) key (ffi/alloc key-layout)
        shape (ffi/alloc shape-layout) transform (ffi/alloc 12) quad (ffi/alloc 16)
        floats (ffi/alloc 12)]
    (try
      (check (not (ffi/null? atlas)) "owned atlas pointer")
      (doseq [[i value] (map-indexed vector [-1.18 -0.68 2.36 1.36])]
        (ffi/write rect :float value (* i 4)))
      (ffi/write key key-layout {:type 0 :codepoint 120 :name ffi/null})
      (println "UINT64-OBSERVED" (u64-low 4) (u64-high 4)
               "RAW-PATH-RESULT" (raw-path-command path 14 rect 4))
      (check (zero? (path-command path 14 rect 4)) "pointer/uint32 path adapter")
      (println "FLOAT-MEMORY-OBSERVED" (read-float rect))
      (println "RAW-FLOAT-RESULT" (define-shape canvas path key 1.0 0 0.0 0.0))
      (ffi/write floats :float 1.0)
      (check (zero? (define-shape-p canvas path key floats)) "float memory adapter + key struct")
      (check (zero? (atlas-build atlas)) "atlas build")
      (check (atlas-built? atlas) "bool result")
      (check (= 1 (get-shape atlas key shape)) "shape output struct")
      (let [result (ffi/read shape shape-layout)]
        (check (near? 2.36 (:width result)) "float width read")
        (check (near? 1.36 (:height result)) "float height read"))
      (ffi/write floats :float 0.5)
      (check (zero? (shape-quad-p shape transform floats quad)) "float memory scale + output pointer")
      (check (near? 1.18 (- (ffi/read quad :float 8) (ffi/read quad :float 0))) "quad span")
      (check (not (zero? (path-command path 999 ffi/null 0))) "invalid command failure")
      (check (pos? (count (last-error))) "borrowed UTF-8 error string")
      (println "SLIPSTREAM-WASM-ABI-PASS")
      (finally
        (doseq [p [rect key shape transform quad floats]] (ffi/free p))
        (path-destroy path) (canvas-destroy canvas) (atlas-destroy atlas)))))
