package eu.kanade.tachiyomi.ui.reader.viewer.webgpu

import ca.mpreg.webgpuviewer.renderer.ImageFilterWgsl
import io.kotest.matchers.shouldBe
import org.junit.jupiter.api.Test
import java.io.File

class SelectiveWhiteTest {
    @Test
    fun `bundled shader declares the supported strength range`() {
        val filter = ImageFilterWgsl(File("src/main/assets/selective_white.wgsl").readText())
        val param = filter.params.single()
        param.name shouldBe "strength"
        param.default shouldBe 0.35f
        param.minimum shouldBe 0f
        param.maximum shouldBe 0.4f
        filter.outputSize(256, 1f) shouldBe 256
        filter.halo(1f) shouldBe 0
    }

    @Test
    fun `preset and parameter survive preference serialization`() {
        val preset = WebGpuShader(WebGpuShaders.WHITE_FILTER_FILE, "Selective white reduction", mapOf("strength" to 0.2f))
        WebGpuShaders.deserialize(WebGpuShaders.serialize(listOf(preset))) shouldBe listOf(preset)
    }
}
