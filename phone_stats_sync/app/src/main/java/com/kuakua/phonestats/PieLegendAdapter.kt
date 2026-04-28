package com.kuakua.phonestats

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.RecyclerView
import com.kuakua.phonestats.databinding.ItemPieLegendBinding
import java.util.Locale

class PieLegendAdapter : RecyclerView.Adapter<PieLegendAdapter.ViewHolder>() {

    private var items = listOf<PieLegendItem>()

    fun updateItems(newItems: List<PieLegendItem>) {
        items = newItems
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemPieLegendBinding.inflate(
            LayoutInflater.from(parent.context), parent, false
        )
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(items[position])
    }

    override fun getItemCount() = items.size

    class ViewHolder(private val binding: ItemPieLegendBinding) : RecyclerView.ViewHolder(binding.root) {
        fun bind(item: PieLegendItem) {
            // 番茄Todo风格马卡龙色调
            val macaronColors = intArrayOf(
                ContextCompat.getColor(itemView.context, R.color.warm_brown_main),
                ContextCompat.getColor(itemView.context, R.color.warm_yellow),
                ContextCompat.getColor(itemView.context, R.color.warm_mint),
                ContextCompat.getColor(itemView.context, R.color.warm_blue),
                ContextCompat.getColor(itemView.context, R.color.warm_purple),
                ContextCompat.getColor(itemView.context, R.color.disabled)
            )

            // 设置颜色点
            val colorIndex = item.colorIndex % macaronColors.size
            binding.colorDot.setBackgroundColor(macaronColors[colorIndex])

            // 格式化时长显示
            val hours = item.durationMinutes / 60
            val minutes = item.durationMinutes % 60
            val durationText = if (hours > 0) {
                String.format(Locale.getDefault(), "%s %d小时%d分钟", item.appName, hours, minutes)
            } else {
                String.format(Locale.getDefault(), "%s %d分钟", item.appName, minutes)
            }

            binding.appNameDuration.text = durationText
            binding.percentage.text = String.format(Locale.getDefault(), "%.1f%%", item.percentage * 100)
        }
    }
}
