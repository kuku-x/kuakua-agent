package com.kuakua.phonestats

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.kuakua.phonestats.databinding.ItemUsageStatsBinding

class UsageStatsAdapter : RecyclerView.Adapter<UsageStatsAdapter.ViewHolder>() {

    private var items = listOf<UsageStatsItem>()

    fun updateItems(newItems: List<UsageStatsItem>) {
        items = newItems
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemUsageStatsBinding.inflate(
            LayoutInflater.from(parent.context), parent, false
        )
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(items[position])
    }

    override fun getItemCount() = items.size

    class ViewHolder(private val binding: ItemUsageStatsBinding) : RecyclerView.ViewHolder(binding.root) {
        fun bind(item: UsageStatsItem) {
            binding.appIcon.setImageDrawable(item.appIcon)
            binding.appName.text = item.appName
            binding.durationText.text = "${item.durationMinutes}分钟"
            binding.progressBar.progress = (item.progressPercent * 100).toInt()
        }
    }
}
