(ns feedback.web
  "Experimental owner-thread Jolt model driving the real Slipstream WebGL scene."
  (:require [jolt.ffi :as ffi]
            [feedback.model :as model]
            [feedback.visuals :as visuals]))

(ffi/defcfn input! "web_scene_input" [:pointer] :int32)
(ffi/defcfn submit! "web_scene_submit" [:pointer] :int32)
(defonce state (atom (model/initial-state)))
;; Buffers live for the module lifetime; C borrows only for each call.
(defonce input-buffer (ffi/alloc (* 9 4)))
(defonce payload (ffi/alloc (* 442 4)))
(defn checked [result]
  (when-not (zero? result) (throw (ex-info "Slipstream web adapter failed" {:code result}))))
(defn frame! []
  (checked (input! input-buffer))
  (let [v (mapv #(double (ffi/read input-buffer :float (* 4 %))) (range 9))
        input {:mouse [(nth v 0) (nth v 1)] :scroll-y (nth v 2)
               :left (pos? (nth v 3)) :right (pos? (nth v 4)) :middle (pos? (nth v 5))
               :space (pos? (nth v 6)) :r (pos? (nth v 7))}
        s (swap! state #(model/advance (model/update-input % input) (nth v 8)))
        effect (visuals/effect s)
        ordered (sort-by (comp str key) (:uniforms effect))
        values (vec (concat
                      (mapcat (fn [[_ {:keys [type value]}]]
                                (if (= type :mat3) value [value])) ordered)
                      [(if (:paused s) 1.0 0.0) (:time s)
                       (get-in s [:camera :zoom]) (get-in s [:camera :pan-x])
                       (get-in s [:camera :pan-y]) (get-in s [:camera :yaw])
                       (get-in s [:camera :pitch]) (get-in s [:camera :roll])] ))]
    (when-not (= 442 (count values))
      (throw (ex-info "Web prototype requires a 48-frame effect" {})))
    (doseq [[i value] (map-indexed vector values)]
      (ffi/write payload :float value (* i 4)))
    (checked (submit! payload))))
(defn -main [& args]
  (println "SLIPSTREAM-JOLT-LIVE-BOOT"))
