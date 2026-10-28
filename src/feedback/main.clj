(ns feedback.main
  (:require [glimmer.core :as ui]
            [glimmer.ratom :as r]
            [slipstream.glimmer :as sg]
            [slipstream.glimmer-renderer :as renderer]
            [feedback.model :as model]
            [feedback.visuals :as visuals])
  (:import [java.io File FileOutputStream]))

(defonce state (r/atom (model/initial-state)))
(def bounds [-1.6 1.6 -1.0 1.0])
(defn default-font []
  (or (System/getenv "SLIPSTREAM_TEST_FONT")
      (first (filter #(.exists (File. %))
                     ["/usr/share/fonts/adwaita-mono-fonts/AdwaitaMono-Regular.ttf"
                      "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
                      "/System/Library/Fonts/Menlo.ttc"]))))
(defn current-mouse [context]
  (try
    (renderer/cursor->bounds context bounds)
    (catch Throwable error
      (if (= "cannot map cursor with an empty window or framebuffer" (ex-message error))
        (get-in @state [:input :mouse] [0.0 0.0])
        (throw error)))))
(defn write-ppm! [path {:keys [width height pixels]}]
  (let [rgb (byte-array (* width height 3))]
    (doseq [y (range height) x (range width) channel (range 3)]
      (aset rgb (+ (* 3 (+ (* y width) x)) channel)
            (aget pixels (+ (* 4 (+ (* (- height y 1) width) x)) channel))))
    (with-open [out (FileOutputStream. path)]
      (.write out (.getBytes (str "P6\n" width " " height "\n255\n") "UTF-8"))
      (.write out rgb))))
(defn parse-args [args]
  (loop [args args options {}]
    (if (empty? args)
      options
      (let [[flag value & more] args]
        (when-not value (throw (ex-info (str "Missing value for " flag) {})))
        (recur more
               (case flag
                 "--font" (assoc options :font value)
                 "--capture" (assoc options :capture value)
                 "--frames" (let [n (parse-long value)]
                              (when-not (and n (pos? n))
                                (throw (ex-info "--frames requires a positive integer" {})))
                              (assoc options :frames n))
                 (throw (ex-info (str "Unknown option: " flag) {}))))))))
(defn start! [{:keys [font frames capture]}]
  (let [font (or font (default-font))
        previous (atom nil)
        rendered (atom 0)]
    (when-not (and font (.exists (File. font)))
      (throw (ex-info "Supply --font /path/font.ttf or SLIPSTREAM_TEST_FONT" {})))
    (when (and capture (nil? frames))
      (throw (ex-info "--capture requires --frames" {})))
    (reset! state (model/initial-state))
    (ui/run #(visuals/scene @state font)
            :title "Picture Plane — Slipstream vector feedback"
            :width 1152 :height 720 :bounds bounds :max-frames frames
            :after-render
            (fn []
              (when-let [context (sg/current-context)]
                (let [now (System/nanoTime)
                      dt (if @previous (/ (- now @previous) 1.0e9) model/tick)
                      input (assoc (renderer/input-snapshot context)
                                   :mouse (current-mouse context))]
                  (reset! previous now)
                  ;; Timed captures use deterministic steps, independent of GPU speed.
                  (swap! state #(model/advance (model/update-input % input)
                                              (if frames model/tick dt)))
                  (when (and capture (= (swap! rendered inc) frames))
                    (write-ppm! capture (renderer/capture! context)))))))))
(defn -main [& args]
  (start! (parse-args args)))
